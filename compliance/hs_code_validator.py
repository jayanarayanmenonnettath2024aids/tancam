from db.models import HsCode

def validate_hs_code(hs_code: str, db_session) -> dict:
    if not hs_code:
        return {"valid": False, "description": None, "flag": "Missing HS Code"}
        
    hs_code = str(hs_code).strip()
    
    # Format check: 6 or 8 digit numeric string
    if len(hs_code) not in [4, 6, 8] or not hs_code.isdigit():
        return {"valid": False, "description": None, "flag": f"Invalid format: {hs_code}"}
        
    record = db_session.query(HsCode).filter(HsCode.code == hs_code).first()
    
    if record:
        return {"valid": True, "description": record.description, "flag": None}
        
    return {"valid": False, "description": None, "flag": f"HS Code {hs_code} not found in reference DB"}
