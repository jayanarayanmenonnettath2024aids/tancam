from rapidfuzz import process, fuzz
import re

def resolve_entity_name(name: str, existing_names: list, threshold=85.0) -> str:
    """
    Finds the best matching entity name from a list of existing canonical names using string similarity.
    If a match > threshold is found, returns the canonical name. Otherwise, returns the original name.
    """
    if not name or not existing_names:
        return str(name).strip() if name else name
        
    clean_target = re.sub(r'[^a-zA-Z0-9\s]', '', str(name)).strip()
    if not clean_target:
        return str(name)
        
    # extractOne returns (match, score, index)
    match_result = process.extractOne(clean_target, existing_names, scorer=fuzz.WRatio)
    
    if match_result:
        best_match, score, _ = match_result
        if score >= threshold:
            return best_match
            
    return str(name).strip()

def resolve_customer(name: str, db_session) -> str:
    """Resolves customer against database records."""
    from db.models import Customer
    existing = [c[0] for c in db_session.query(Customer.canonical_name).all()]
    return resolve_entity_name(name, existing)

def resolve_product(name: str, db_session) -> str:
    """Resolves product against database records."""
    from db.models import Product
    existing = [p[0] for p in db_session.query(Product.canonical_name).all()]
    return resolve_entity_name(name, existing)
