import os
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from db.models import Invoice, Shipment, ComplianceRecord, AnomalyRecord, Customer
import spacy
import re
import time

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If not loaded, download on the fly (for robustness in dev)
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def process_query(query_text: str, db_session) -> dict:
    start = time.time()
    
    query_lower = query_text.lower()
    doc = nlp(query_text)
    
    intent = "GENERAL"
    entities = {}
    
    # 1. Intent Detection via Keywords
    if "total" in query_lower and ("value" in query_lower or "export" in query_lower):
        intent = "TOTAL_VALUE"
    elif "count" in query_lower or "how many" in query_lower:
        if "pending" in query_lower:
            intent = "COUNT_PENDING"
        elif "shipment" in query_lower:
            intent = "COUNT_SHIPMENTS"
    elif "top" in query_lower and "customer" in query_lower:
        intent = "TOP_N_CUSTOMERS"
    elif "status" in query_lower and ("shipment" in query_lower or "invoice" in query_lower):
        intent = "STATUS_CHECK"
    elif "compliance" in query_lower or "alert" in query_lower:
        intent = "COMPLIANCE_ALERTS"
    elif "anomaly" in query_lower or "suspicious" in query_lower:
        intent = "ANOMALY_CHECK"
        
    # 2. Entity Extraction
    # Extract numbers for TOP_N
    for ent in doc.ents:
        if ent.label_ == "CARDINAL" or ent.label_ == "DATE":
            entities[ent.label_] = ent.text
            
    # Try Regex for N if spacy missed it
    if intent == "TOP_N_CUSTOMERS" and "CARDINAL" not in entities:
        match = re.search(r'\btop\s+(\d+)\b', query_lower)
        if match:
            entities["CARDINAL"] = match.group(1)
            
    # Invoice extractor
    inv_match = re.search(r'(inv[-_]?\d+)', query_lower)
    if inv_match:
        entities["INVOICE_NO"] = inv_match.group(1).upper()
        
    # 3. SQL Execution & formatting
    answer = "I'm not sure how to answer that yet."
    data = []
    sql_executed = ""
    
    now = datetime.datetime.utcnow()
    
    try:
        if intent == "TOTAL_VALUE":
            date_filter = now.replace(day=1, hour=0, minute=0, second=0)
            if "last month" in query_lower:
                date_filter = now.replace(day=1) - relativedelta(months=1)
                sql_executed = "SELECT SUM(total_value) FROM invoices WHERE invoice_date >= date_trunc('month', NOW() - INTERVAL '1 month') AND invoice_date < date_trunc('month', NOW())"
                val = db_session.query(func.sum(Invoice.total_value)).filter(
                    Invoice.invoice_date >= date_filter,
                    Invoice.invoice_date < now.replace(day=1)
                ).scalar() or 0
                answer = f"Total trade value last month was ₹{val:,.0f}"
            else:
                # default this month
                sql_executed = "SELECT SUM(total_value) FROM invoices WHERE invoice_date >= date_trunc('month', NOW())"
                val = db_session.query(func.sum(Invoice.total_value)).filter(Invoice.invoice_date >= date_filter).scalar() or 0
                answer = f"Total trade value this month is ₹{val:,.0f}"
                
        elif intent == "COUNT_PENDING":
            sql_executed = "SELECT COUNT(*) FROM shipments WHERE status='pending'"
            val = db_session.query(func.count(Shipment.id)).filter(Shipment.status == 'pending').scalar() or 0
            answer = f"There are {val} pending shipments right now."
            
        elif intent == "TOP_N_CUSTOMERS":
            limit = int(entities.get("CARDINAL", 5))
            sql_executed = f"SELECT buyer, SUM(total_value) as val FROM invoices GROUP BY buyer ORDER BY val DESC LIMIT {limit}"
            results = db_session.query(Invoice.buyer, func.sum(Invoice.total_value).label('val')).filter(Invoice.buyer.isnot(None)).group_by(Invoice.buyer).order_by(func.sum(Invoice.total_value).desc()).limit(limit).all()
            
            data = [{"customer": r[0], "value": r[1]} for r in results]
            names_str = ", ".join([f"{i+1}. {r[0]} (₹{r[1]:,.0f})" for i, r in enumerate(results)])
            answer = f"Top {limit} customers by value: {names_str}"
            
        elif intent == "STATUS_CHECK" and "INVOICE_NO" in entities:
            inv = entities["INVOICE_NO"]
            sql_executed = f"SELECT * FROM shipments WHERE invoice_no ILIKE '%{inv}%'"
            shipment = db_session.query(Shipment).filter(Shipment.invoice_no.ilike(f"%{inv}%")).first()
            if shipment:
                answer = f"Shipment {shipment.invoice_no}: status is {shipment.status.upper()}, loading at {shipment.port_of_loading}."
                data = [{"id": shipment.id, "status": shipment.status}]
            else:
                answer = f"Could not find a shipment for invoice {inv}."
                
        elif intent == "COMPLIANCE_ALERTS":
            sql_executed = "SELECT COUNT(*) FROM compliance_records WHERE overall_status IN ('warning','critical')"
            val = db_session.query(func.count(ComplianceRecord.id)).filter(ComplianceRecord.overall_status.in_(['warning', 'critical'])).scalar() or 0
            answer = f"There are {val} active compliance alerts."
            
        elif intent == "ANOMALY_CHECK":
            sql_executed = "SELECT COUNT(*) FROM anomaly_records WHERE is_anomaly = true AND detected_at >= NOW() - INTERVAL '7 days'"
            date_filter = now - datetime.timedelta(days=7)
            val = db_session.query(func.count(AnomalyRecord.id)).filter(AnomalyRecord.is_anomaly == True, AnomalyRecord.detected_at >= date_filter).scalar() or 0
            answer = f"{val} suspicious records detected in the last 7 days."
            
        else:
            answer = "I couldn't quite understand that. Try asking about 'pending shipments' or 'top customers'."
            
    except Exception as e:
        answer = f"Failed to execute query: {str(e)}"
        
    return {
        "answer": answer,
        "intent": intent,
        "entities": entities,
        "sql_executed": sql_executed,
        "data": data,
        "record_count": len(data) if data else 0,
        "query_ms": int((time.time() - start) * 1000)
    }
