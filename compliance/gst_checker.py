import re

def validate_mod36(gstin: str) -> bool:
    """Validates the mod 36 checksum of a GSTIN."""
    char_map = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if not gstin or len(gstin) != 15:
        return False
        
    chars = gstin[:-1]
    check = gstin[-1]
    
    total = 0
    for i, c in enumerate(chars):
        val = char_map.index(c)
        factor = 2 if i % 2 == 1 else 1 # Alternate 2 and 1
        
        prod = val * factor
        quotient = prod // 36
        remainder = prod % 36
        total += (quotient + remainder)
        
    calc_check_val = (36 - (total % 36)) % 36
    calc_check = char_map[calc_check_val]
    
    return calc_check == check

def check_gstin(gstin: str) -> dict:
    if not gstin:
        return {"valid": False, "flag": "Missing GSTIN"}
        
    gstin = gstin.strip().upper()
    
    # Pre-2018 format regex logic
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    
    # Let's be a bit lenient on the Z for non-strict testing if needed,
    # but the instructions specified the exact regex.
    if not re.match(pattern, gstin):
        return {"valid": False, "flag": f"Invalid format for GSTIN {gstin}"}
        
    try:
        if not validate_mod36(gstin):
             return {"valid": False, "flag": "Checksum failed for GSTIN"}
    except Exception:
        return {"valid": False, "flag": "Invalid characters in GSTIN"}
        
    return {"valid": True, "flag": None}

def check_gst_amount(invoice_value: float, gst_amount: float, gst_rate: float) -> dict:
    if invoice_value is None or gst_amount is None or gst_rate is None:
        return {"valid": False, "expected": 0, "actual": 0, "flag": "Missing amount fields"}
        
    expected = invoice_value * (gst_rate / 100.0)
    tolerance = 1.0 # ₹1 rounding tolerance
    
    valid = abs(expected - gst_amount) <= tolerance
    return {
         "valid": valid,
         "expected": round(expected, 2),
         "actual": round(gst_amount, 2),
         "flag": f"Expected ₹{expected:.2f} but got ₹{gst_amount:.2f}" if not valid else None
    }
