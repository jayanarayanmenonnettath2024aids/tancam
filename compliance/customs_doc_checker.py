from db.models import Invoice

def check_required_docs(shipment_id, db_session) -> dict:
    present = []
    missing = []
    
    # 1. Invoice
    invoice = db_session.query(Invoice).filter(Invoice.shipment_id == shipment_id).first()
    if invoice:
        present.append("invoice")
    else:
        missing.append("invoice")
        
    # Since we are not strictly indexing TradeDocument to shipment_id due to raw nature, 
    # we will rely on Invoice for MVP / Hackathon.
    # In a full app, we would query TradeDocument examining extracted_json or DB references.
    
    # For now, let's pretend we have a bol if the shipment has a port_of_discharge.
    from db.models import Shipment
    shipment = db_session.query(Shipment).filter(Shipment.id == shipment_id).first()
    if shipment and shipment.port_of_discharge:
        present.append("bill_of_lading")
    else:
        missing.append("bill_of_lading")
        
    # Just a mock check for remaining required docs for demo
    missing.extend(["packing_list", "certificate_of_origin"])
    
    flag = f"Missing: {', '.join(missing)}" if missing else None
    
    return {
        "missing": missing,
        "present": present,
        "complete": len(missing) == 0,
        "flag": flag
    }
