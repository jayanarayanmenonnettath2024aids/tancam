import datetime
from db.models import ComplianceRecord, Shipment, Invoice, Customer, Product
from compliance.gst_checker import check_gstin, check_gst_amount
from compliance.hs_code_validator import validate_hs_code
from compliance.customs_doc_checker import check_required_docs

def run_compliance_check(shipment_id, db_session):
    shipment = db_session.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return None
        
    invoice = db_session.query(Invoice).filter(Invoice.shipment_id == shipment_id).first()
    
    # Run Checks
    gstin_result = {"valid": True, "flag": None}
    hs_result = {"valid": True, "flag": None}
    amount_result = {"valid": True, "flag": None}
    docs_result = {"missing": [], "present": [], "complete": True, "flag": None}
    
    if invoice:
        # Check GSTIN of buyer if we can resolve them
        customer = db_session.query(Customer).filter(Customer.canonical_name == invoice.buyer).first()
        if customer and customer.gstin:
            gstin_result = check_gstin(customer.gstin)
            
        # Check amount
        if invoice.gst_amount is not None and invoice.gst_rate is not None:
             amount_result = check_gst_amount(invoice.total_value, invoice.gst_amount, invoice.gst_rate)
             
    if shipment.product_id:
        product = db_session.query(Product).filter(Product.master_id == shipment.product_id).first()
        if product and product.hs_code:
            hs_result = validate_hs_code(product.hs_code, db_session)
            
    docs_result = check_required_docs(shipment_id, db_session)
    
    # Evaluate Rules
    # "ok" -> all pass
    # "critical" -> GSTIN invalid OR missing invoice doc
    # "warning" -> 1-2 checks fail (non-critical)
    status = "ok"
    
    critical = False
    warning_count = 0
    
    if not gstin_result["valid"] or "invoice" in docs_result["missing"]:
        critical = True
        
    if not hs_result["valid"]:
        warning_count += 1
    if not amount_result["valid"]:
        warning_count += 1
    if len(docs_result["missing"]) > 0 and "invoice" not in docs_result["missing"]:
        warning_count += 1
        
    if critical:
        status = "critical"
    elif warning_count > 0:
        status = "warning"
        
    # Upsert Record
    record = db_session.query(ComplianceRecord).filter(
        ComplianceRecord.shipment_id == shipment_id
    ).first()
    
    if not record:
        record = ComplianceRecord(shipment_id=shipment_id)
        if invoice:
            record.invoice_id = invoice.id
        db_session.add(record)
        
    record.gstin_valid = gstin_result["valid"]
    record.gstin_flag = gstin_result["flag"]
    record.hs_code_valid = hs_result["valid"]
    record.hs_code_flag = hs_result["flag"]
    record.gst_amount_valid = amount_result["valid"]
    record.gst_amount_flag = amount_result["flag"]
    record.missing_docs = docs_result["missing"]
    record.overall_status = status
    record.checked_at = datetime.datetime.utcnow()
    
    db_session.commit()
    return record
