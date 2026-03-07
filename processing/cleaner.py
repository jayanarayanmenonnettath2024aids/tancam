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

def clean_dataframe(df):
    """
    Applies cleaning transformations to a pandas DataFrame of trade records.
    Standardizes column names, cleans monetary values, parses dates, and drops empty rows.
    Returns the cleaned DataFrame.
    """
    import pandas as pd

    df = df.copy()

    # Normalize column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Clean monetary/numeric columns
    money_cols = [c for c in df.columns if any(k in c for k in ['value', 'amount', 'price', 'duty', 'rate', 'qty', 'quantity'])]
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_amount)

    # Parse date columns
    date_cols = [c for c in df.columns if 'date' in c]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    # Standardize GSTIN
    if 'gst_id' in df.columns:
        df['gst_id'] = df['gst_id'].apply(standardize_gstin)
    if 'gstin' in df.columns:
        df['gstin'] = df['gstin'].apply(standardize_gstin)

    # Drop rows that are entirely empty
    df = df.dropna(how='all')

    return df
