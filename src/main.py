"""
Main orchestration script for apartment listing monitor.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SEEN_LISTINGS_FILE
from src.scraper import scrape_listings, Listing
from src.filters import apply_all_filters
from src.notifier import notify_new_listings


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_seen_listings() -> set[str]:
    """Load previously seen listing IDs from file."""
    filepath = get_project_root() / SEEN_LISTINGS_FILE

    if not filepath.exists():
        return set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get("seen_ids", []))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load seen listings: {e}")
        return set()


def save_seen_listings(seen_ids: set[str], new_listings: list[Listing]) -> None:
    """Save seen listing IDs to file."""
    filepath = get_project_root() / SEEN_LISTINGS_FILE
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data to save
    data = {
        "seen_ids": list(seen_ids),
        "last_updated": datetime.utcnow().isoformat(),
        "last_new_count": len(new_listings),
        "recent_listings": [
            {
                "id": l.id,
                "title": l.title[:100],
                "price": l.price_eur,
                "size": l.size_m2,
                "added": datetime.utcnow().isoformat(),
            }
            for l in new_listings[:10]  # Keep last 10 new listings for reference
        ]
    }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(seen_ids)} seen listing IDs")
    except IOError as e:
        print(f"Error saving seen listings: {e}")


def find_new_listings(filtered_listings: list[Listing], seen_ids: set[str]) -> list[Listing]:
    """Find listings that haven't been seen before."""
    new_listings = []

    for listing in filtered_listings:
        if listing.id not in seen_ids:
            new_listings.append(listing)

    return new_listings


def run_monitor(max_pages: int = 3, dry_run: bool = False) -> dict:
    """
    Run the apartment monitor.

    Args:
        max_pages: Maximum pages to scrape from ss.lv
        dry_run: If True, don't send notifications or update state

    Returns:
        Summary dictionary with statistics
    """
    print("=" * 60)
    print(f"Apartment Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Scrape listings
    print("\n📥 Scraping ss.lv listings...")
    all_listings = scrape_listings(max_pages=max_pages)
    print(f"Found {len(all_listings)} total listings")

    if not all_listings:
        print("No listings found. Check if ss.lv is accessible.")
        return {
            "total_scraped": 0,
            "total_filtered": 0,
            "new_count": 0,
            "notified": 0,
        }

    # Step 2: Apply filters
    print("\n🔍 Applying filters...")
    filtered_listings = apply_all_filters(all_listings)
    print(f"After filtering: {len(filtered_listings)} listings match criteria")

    # Step 3: Find new listings
    print("\n🆕 Checking for new listings...")
    seen_ids = load_seen_listings()
    print(f"Previously seen: {len(seen_ids)} listings")

    new_listings = find_new_listings(filtered_listings, seen_ids)
    print(f"New listings found: {len(new_listings)}")

    # Step 4: Notify about new listings
    notified_count = 0
    if new_listings:
        print("\n📬 Sending notifications...")
        if dry_run:
            print("[DRY RUN] Would notify about:")
            for listing in new_listings:
                print(f"  - {listing.title}")
                print(f"    Price: {listing.price_eur} EUR, Size: {listing.size_m2} m²")
                print(f"    URL: {listing.url}")
        else:
            notified_count = notify_new_listings(new_listings)
            print(f"Sent {notified_count} notifications")
    else:
        print("\n✓ No new listings matching criteria")

    # Step 5: Update seen listings
    if not dry_run:
        # Add all filtered listings to seen (not just new ones)
        # This ensures we don't re-notify about filtered listings
        for listing in filtered_listings:
            seen_ids.add(listing.id)

        save_seen_listings(seen_ids, new_listings)

    # Summary
    summary = {
        "total_scraped": len(all_listings),
        "total_filtered": len(filtered_listings),
        "new_count": len(new_listings),
        "notified": notified_count,
    }

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total scraped: {summary['total_scraped']}")
    print(f"  Matched filters: {summary['total_filtered']}")
    print(f"  New listings: {summary['new_count']}")
    print(f"  Notifications sent: {summary['notified']}")
    print("=" * 60)

    return summary


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Riga Apartment Listing Monitor")
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Number of pages to scrape (default: 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending notifications or updating state"
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Test Telegram connection and exit"
    )

    args = parser.parse_args()

    if args.test_telegram:
        from src.notifier import test_telegram_connection
        success = test_telegram_connection()
        sys.exit(0 if success else 1)

    summary = run_monitor(max_pages=args.pages, dry_run=args.dry_run)

    # Exit with error if we found listings but couldn't notify
    if summary["new_count"] > 0 and summary["notified"] == 0:
        print("\nWarning: Found new listings but couldn't send notifications!")
        print("Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")


if __name__ == "__main__":
    main()
