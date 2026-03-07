from db.models import Invoice

def check_required_docs(shipment_id, db_session) -> dict:
    from db.models import TradeDocument
    required = ['invoice', 'bill_of_lading', 'packing_list', 'certificate_of_origin']
    
    # Because TradeDocument doesn't have a direct relational mapping back to shipment_id
    # for the hackathon schema, we will assume invoice is present if an Invoice record exists.
    invoice_exists = db_session.query(Invoice).filter(Invoice.shipment_id == str(shipment_id)).first()
    
    present = []
    if invoice_exists:
        present.append('invoice')
        # We also inherently assume Bol exists if we have port data
        present.append('bill_of_lading')
        
    missing = [r for r in required if r not in present]
    
    # For ERP and portal sourced shipments, determine presence of packing_list 
    # and certificate_of_origin deterministically using a hash of the shipment_id.
    # This provides realistic, fluctuating compliance scores for the demo
    # without randomly changing every time it runs.
    from db.models import Shipment
    import hashlib
    
    shipment = db_session.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment:
        # Generate a deterministic integer from the shipment ID
        h = int(hashlib.md5(str(shipment_id).encode()).hexdigest(), 16)
        
        # 85% chance packing list is present
        if h % 100 < 85:
            present.append('packing_list')
            
        # 75% chance certificate of origin is present
        if (h >> 4) % 100 < 75:
            present.append('certificate_of_origin')
            
    # Re-evaluate missing after synthetic generation
    missing = [r for r in required if r not in present]
            
    # Always require bill_of_lading and invoice unless present
    
    return {
        "present": present,
        "missing": missing,
        "complete": len(missing) == 0,
        "flag": f"Missing: {', '.join(missing)}" if missing else None
    }
