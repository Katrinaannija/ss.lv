"""
Scraper module for ss.lv apartment listings.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

from config import SS_LV_BASE_URL, SS_LV_LISTINGS_URL


@dataclass
class Listing:
    """Represents an apartment listing."""
    id: str
    url: str
    title: str
    address: str
    rooms: Optional[int]
    size_m2: Optional[float]
    floor: Optional[str]
    price_eur: Optional[float]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "address": self.address,
            "rooms": self.rooms,
            "size_m2": self.size_m2,
            "floor": self.floor,
            "price_eur": self.price_eur,
        }


def fetch_page(url: str, retry_count: int = 3) -> Optional[str]:
    """Fetch a page with retries."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "lv,en;q=0.9",
    }

    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Fetch attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return None


def parse_price(price_text: str) -> Optional[float]:
    """Extract numeric price from text like '450 €' or '450 €/mēn.'"""
    if not price_text:
        return None
    # Remove non-numeric characters except dots
    cleaned = re.sub(r'[^\d.]', '', price_text.replace(',', '.'))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_size(size_text: str) -> Optional[float]:
    """Extract size in m² from text like '45 m²' or '45'"""
    if not size_text:
        return None
    cleaned = re.sub(r'[^\d.]', '', size_text.replace(',', '.'))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_rooms(rooms_text: str) -> Optional[int]:
    """Extract room count from text."""
    if not rooms_text:
        return None
    cleaned = re.sub(r'[^\d]', '', rooms_text)
    try:
        return int(cleaned) if cleaned else None
    except ValueError:
        return None


def extract_listing_id(url: str) -> str:
    """Extract unique listing ID from URL."""
    # ss.lv URLs look like: /msg/lv/real-estate/flats/riga/centre/abcde.html
    match = re.search(r'/([a-zA-Z0-9]+)\.html', url)
    return match.group(1) if match else url


def scrape_listings(max_pages: int = 3) -> list[Listing]:
    """
    Scrape apartment listings from ss.lv Riga centre.

    Args:
        max_pages: Maximum number of pages to scrape

    Returns:
        List of Listing objects
    """
    listings = []

    for page_num in range(1, max_pages + 1):
        # First page has no page parameter, subsequent pages use page{num}.html
        if page_num == 1:
            url = SS_LV_LISTINGS_URL
        else:
            url = f"{SS_LV_LISTINGS_URL}page{page_num}.html"

        print(f"Fetching page {page_num}: {url}")
        html = fetch_page(url)

        if not html:
            print(f"Failed to fetch page {page_num}")
            continue

        page_listings = parse_listings_page(html)
        listings.extend(page_listings)

        print(f"Found {len(page_listings)} listings on page {page_num}")

        # Be nice to the server
        if page_num < max_pages:
            time.sleep(1)

    return listings


def parse_listings_page(html: str) -> list[Listing]:
    """Parse a single page of listings."""
    soup = BeautifulSoup(html, 'html.parser')
    listings = []

    # ss.lv uses a table with id 'filter_frm' for listings
    # Each listing row has class 'msg2' or similar
    # The table structure: description | address | rooms | m² | floor | price

    # Find all listing rows - they typically have 'tr' with specific ID pattern
    rows = soup.find_all('tr', id=re.compile(r'^tr_\d+'))

    if not rows:
        # Alternative: look for rows with msg2 class
        rows = soup.find_all('tr', class_=re.compile(r'msg\d?'))

    for row in rows:
        try:
            listing = parse_listing_row(row)
            if listing:
                listings.append(listing)
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return listings


def parse_listing_row(row) -> Optional[Listing]:
    """Parse a single listing row from the table."""
    # Get all cells
    cells = row.find_all('td')

    if len(cells) < 6:
        return None

    # Find the link to the listing
    link = row.find('a', class_='am')
    if not link:
        # Try alternative link patterns
        link = row.find('a', href=re.compile(r'/msg/'))

    if not link:
        return None

    href = link.get('href', '')
    if not href:
        return None

    # Build full URL
    if href.startswith('/'):
        url = SS_LV_BASE_URL + href
    else:
        url = href

    listing_id = extract_listing_id(href)
    title = link.get_text(strip=True)

    # Parse cells - typical order: description, street, rooms, m², floor, price
    # The exact order may vary, so we try to be flexible
    address = ""
    rooms = None
    size_m2 = None
    floor = None
    price_eur = None

    # Usually: cell[0] = checkbox, cell[1] = image, cell[2] = description
    # cell[3] = street, cell[4] = rooms, cell[5] = m², cell[6] = floor, cell[7] = price

    for i, cell in enumerate(cells):
        text = cell.get_text(strip=True)

        # Skip empty cells
        if not text:
            continue

        # Check for address (contains street names or "iela", "bulvāris")
        if any(street_indicator in text.lower() for street_indicator in ['iela', 'bulv', 'gatve', 'šķērsiela', ',']):
            if not address:  # Take first matching cell as address
                address = text

        # Check for price (contains € or EUR)
        if '€' in text or 'EUR' in text or 'eur' in text.lower():
            price_eur = parse_price(text)

        # Check for size (contains m² or m2)
        if 'm²' in text or 'm2' in text.lower():
            size_m2 = parse_size(text)

        # Check for standalone numbers that could be rooms or size
        if text.isdigit():
            num = int(text)
            if num < 10 and rooms is None:  # Likely rooms
                rooms = num
            elif 15 <= num <= 500 and size_m2 is None:  # Likely size
                size_m2 = float(num)

        # Floor pattern (e.g., "2/5" or "3/9")
        if re.match(r'^\d+/\d+$', text):
            floor = text

    # If we still don't have address, use title as fallback
    if not address:
        address = title

    return Listing(
        id=listing_id,
        url=url,
        title=title,
        address=address,
        rooms=rooms,
        size_m2=size_m2,
        floor=floor,
        price_eur=price_eur,
    )


if __name__ == "__main__":
    # Test scraper
    print("Testing scraper...")
    listings = scrape_listings(max_pages=1)
    print(f"\nFound {len(listings)} total listings")

    for listing in listings[:5]:
        print(f"\n{listing.title}")
        print(f"  Address: {listing.address}")
        print(f"  Size: {listing.size_m2} m²")
        print(f"  Price: {listing.price_eur} EUR")
        print(f"  URL: {listing.url}")
