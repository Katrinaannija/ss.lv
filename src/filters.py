"""
Filtering module for apartment listings.
Applies criteria: price, size, street location, street number.
"""

import re
from typing import Optional

from src.scraper import Listing
from config import MIN_PRICE, MAX_PRICE, MIN_SIZE, MAX_STREET_NUMBER, ALLOWED_STREETS


def normalize_street_name(street: str) -> str:
    """Normalize street name for comparison."""
    return street.lower().strip()


def extract_street_number(address: str) -> Optional[int]:
    """
    Extract street number from address.
    Examples:
        "Ģertrūdes iela 12" -> 12
        "K. Barona 45-3" -> 45
        "Dzirnavu 67/69" -> 67
    """
    if not address:
        return None

    # Look for number patterns at the end or after street name
    # Pattern: number possibly followed by apartment/building suffix
    patterns = [
        r'(\d+)\s*[-/]\s*\d+',  # 45-3 or 67/69
        r'(\d+)\s*[a-zA-Z]?\s*$',  # 45 or 45a at end
        r'iela\s+(\d+)',  # iela 45
        r'bulvāris\s+(\d+)',  # bulvāris 45
        r'[,\s]+(\d+)',  # , 45 or space 45
    ]

    for pattern in patterns:
        match = re.search(pattern, address, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return None


def is_allowed_street(address: str) -> bool:
    """
    Check if the address is on one of the allowed streets.
    """
    if not address:
        return False

    normalized_address = normalize_street_name(address)

    for street in ALLOWED_STREETS:
        normalized_street = normalize_street_name(street)
        if normalized_street in normalized_address:
            return True

    return False


def get_matching_street(address: str) -> Optional[str]:
    """
    Return the name of the matching allowed street, if any.
    """
    if not address:
        return None

    normalized_address = normalize_street_name(address)

    for street in ALLOWED_STREETS:
        normalized_street = normalize_street_name(street)
        if normalized_street in normalized_address:
            return street

    return None


def filter_by_price(listing: Listing) -> bool:
    """Check if listing is within price range (250-500 EUR)."""
    if listing.price_eur is None:
        # Reject listings without price
        return False
    return MIN_PRICE <= listing.price_eur <= MAX_PRICE


def filter_by_size(listing: Listing) -> bool:
    """Check if listing meets minimum size requirement."""
    if listing.size_m2 is None:
        # If size is unknown, include it (will be checked manually)
        return True
    return listing.size_m2 >= MIN_SIZE


def filter_by_street(listing: Listing) -> bool:
    """Check if listing is on an allowed street."""
    return is_allowed_street(listing.address) or is_allowed_street(listing.title)


def filter_by_street_number(listing: Listing) -> bool:
    """Check if street number is within allowed range (central area)."""
    # Try to extract from address first, then title
    number = extract_street_number(listing.address)
    if number is None:
        number = extract_street_number(listing.title)

    if number is None:
        # If we can't determine the number, include it (will be checked manually)
        return True

    return number <= MAX_STREET_NUMBER


def apply_all_filters(listings: list[Listing]) -> list[Listing]:
    """
    Apply all filters to a list of listings.
    Returns only listings that match ALL criteria.
    """
    filtered = []

    for listing in listings:
        # Check all criteria
        price_ok = filter_by_price(listing)
        size_ok = filter_by_size(listing)
        street_ok = filter_by_street(listing)
        number_ok = filter_by_street_number(listing)

        if price_ok and size_ok and street_ok and number_ok:
            filtered.append(listing)
        else:
            # Debug output for rejected listings
            reasons = []
            if not price_ok:
                if listing.price_eur is None:
                    reasons.append("no price")
                else:
                    reasons.append(f"price={listing.price_eur} (need {MIN_PRICE}-{MAX_PRICE})")
            if not size_ok:
                reasons.append(f"size={listing.size_m2}")
            if not street_ok:
                reasons.append("street not allowed")
            if not number_ok:
                reasons.append(f"street number > {MAX_STREET_NUMBER}")

            print(f"Filtered out: {listing.title[:50]}... ({', '.join(reasons)})")

    return filtered


def get_filter_summary(listing: Listing) -> dict:
    """
    Get a summary of filter results for a listing.
    Useful for debugging.
    """
    return {
        "price_ok": filter_by_price(listing),
        "size_ok": filter_by_size(listing),
        "street_ok": filter_by_street(listing),
        "number_ok": filter_by_street_number(listing),
        "matched_street": get_matching_street(listing.address) or get_matching_street(listing.title),
        "extracted_number": extract_street_number(listing.address) or extract_street_number(listing.title),
    }


if __name__ == "__main__":
    # Test filter functions
    print("Testing street matching...")

    test_addresses = [
        "Ģertrūdes iela 25",
        "K. Barona 45-3",
        "Dzirnavu 67",
        "Maskavas iela 100",  # Not in allowed list
        "Čaka iela 88",
        "Brīvības bulvāris 150",  # Number too high
        "Lāčplēša 15",
    ]

    for addr in test_addresses:
        is_allowed = is_allowed_street(addr)
        number = extract_street_number(addr)
        matched = get_matching_street(addr)
        print(f"{addr}")
        print(f"  Allowed: {is_allowed}, Street: {matched}, Number: {number}")
        print()
