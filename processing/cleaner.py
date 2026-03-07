import re
from dateutil.parser import parse

def clean_amount(val) -> float:
    """Extracts numeric float from a string like '₹ 10,000.50'."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return 0.0
        
    val = str(val).replace(",", "").replace(u"₹", "").replace("$", "").replace("Rs", "").strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val)
    return float(match.group()) if match else 0.0

def clean_date(val):
    """Parses various date string formats into standard Python date."""
    if not val:
        return None
    try:
        # Handles 2026-03-29, 29/03/2026, Mar 29 2026, etc.
        dt = parse(str(val))
        return dt.date()
    except Exception:
        return None

def standardize_gstin(val: str) -> str:
    """Removes spaces and standardizes GSTIN."""
    if not val:
        return None
    return str(val).strip().upper()

def clean_quantity(val) -> float:
    """Extracts base quantity."""
    return clean_amount(val)
