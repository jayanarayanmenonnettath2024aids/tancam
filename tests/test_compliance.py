import pytest
from compliance.gst_checker import check_gstin, check_gst_amount

def test_gstin_valid():
    # A mathematically valid mock GSTIN passing Mod36 Checksum
    result = check_gstin("07AAGFF2194N1Z1")
    assert result["valid"] is True
    assert result["flag"] is None

def test_gstin_invalid_length():
    result = check_gstin("27AAAAA0000A1Z") # 14 chars
    assert result["valid"] is False
    assert "Invalid format" in result["flag"]

def test_gst_amount_correct():
    # Value 1000, rate 18%, amount should be 180
    result = check_gst_amount(1000.0, 180.0, 18.0)
    assert result["valid"] is True

def test_gst_amount_incorrect():
    # Value 1000, rate 18%, amount is 150 (incorrect)
    result = check_gst_amount(1000.0, 150.0, 18.0)
    assert result["valid"] is False
    assert "Expected ₹180.00 but got" in result["flag"]
