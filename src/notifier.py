"""
Telegram notification module for apartment listings.
"""

import os
import requests
from typing import Optional

from src.scraper import Listing
from src.filters import get_matching_street, extract_street_number


def get_telegram_config() -> tuple[Optional[str], Optional[str]]:
    """Get Telegram bot token and chat ID from environment."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return bot_token, chat_id


def format_listing_message(listing: Listing) -> str:
    """Format a listing as a Telegram message."""
    # Build message with available info
    lines = ["🏠 *New Apartment Listing!*", ""]

    # Address/Title
    street = get_matching_street(listing.address) or get_matching_street(listing.title)
    number = extract_street_number(listing.address) or extract_street_number(listing.title)

    if street and number:
        lines.append(f"📍 *{street} {number}*")
    elif listing.address:
        lines.append(f"📍 {listing.address}")
    else:
        lines.append(f"📍 {listing.title}")

    lines.append("")

    # Details
    if listing.price_eur:
        lines.append(f"💰 Price: *{listing.price_eur:.0f} EUR/month*")

    if listing.size_m2:
        lines.append(f"📐 Size: *{listing.size_m2:.0f} m²*")

    if listing.rooms:
        lines.append(f"🚪 Rooms: {listing.rooms}")

    if listing.floor:
        lines.append(f"🏢 Floor: {listing.floor}")

    lines.append("")
    lines.append(f"🔗 [View on ss.lv]({listing.url})")

    return "\n".join(lines)


def send_telegram_message(message: str, bot_token: str, chat_id: str) -> bool:
    """
    Send a message via Telegram bot.

    Args:
        message: The message to send (supports Markdown)
        bot_token: Telegram bot token
        chat_id: Target chat ID

    Returns:
        True if successful, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if result.get("ok"):
            return True
        else:
            print(f"Telegram API error: {result.get('description', 'Unknown error')}")
            return False

    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False


def notify_new_listings(listings: list[Listing]) -> int:
    """
    Send notifications for new listings.

    Args:
        listings: List of new listings to notify about

    Returns:
        Number of successfully sent notifications
    """
    bot_token, chat_id = get_telegram_config()

    if not bot_token or not chat_id:
        print("Warning: Telegram credentials not configured.")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        print("\nWould have sent notifications for:")
        for listing in listings:
            print(f"  - {listing.title} ({listing.price_eur} EUR, {listing.size_m2} m²)")
        return 0

    sent_count = 0

    for listing in listings:
        message = format_listing_message(listing)
        if send_telegram_message(message, bot_token, chat_id):
            sent_count += 1
            print(f"✓ Notified: {listing.title[:50]}...")
        else:
            print(f"✗ Failed to notify: {listing.title[:50]}...")

    return sent_count


def send_summary_message(total_scraped: int, total_filtered: int, new_count: int) -> bool:
    """
    Send a summary message about the monitoring run.
    Only sends if there were no new listings (as a heartbeat).
    """
    bot_token, chat_id = get_telegram_config()

    if not bot_token or not chat_id:
        return False

    if new_count > 0:
        # Don't send summary if we already sent listing notifications
        return True

    # Optional: Send periodic "still running" message
    # Uncomment if you want heartbeat messages
    # message = (
    #     f"📊 *Monitor Status*\n\n"
    #     f"Checked: {total_scraped} listings\n"
    #     f"Matched filters: {total_filtered}\n"
    #     f"New listings: {new_count}\n\n"
    #     f"_No new apartments matching your criteria._"
    # )
    # return send_telegram_message(message, bot_token, chat_id)

    return True


def test_telegram_connection() -> bool:
    """Test if Telegram bot is configured and working."""
    bot_token, chat_id = get_telegram_config()

    if not bot_token or not chat_id:
        print("Telegram not configured. Set environment variables:")
        print("  TELEGRAM_BOT_TOKEN")
        print("  TELEGRAM_CHAT_ID")
        return False

    message = "✅ *Apartment Monitor Connected!*\n\nYou will receive notifications for new listings."
    return send_telegram_message(message, bot_token, chat_id)


if __name__ == "__main__":
    print("Testing Telegram connection...")
    if test_telegram_connection():
        print("Success! Telegram is working.")
    else:
        print("Failed to connect to Telegram.")
