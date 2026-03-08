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

def process_query(query_text: str, db_session, user=None) -> dict:
    start = time.time()
    
    query_lower = query_text.lower()
    doc = nlp(query_text)
    
    intent = "GENERAL"
    entities = {}
    
    # 0. Local LLM Intent Detection
    from ml.llm_service import get_intent_from_llm
    llm_intent, llm_conf = get_intent_from_llm(query_text)
    
    # Let LLM override if confidence is relatively high
    if llm_intent != "GENERAL" and llm_conf >= 0.4:
        intent = llm_intent
        confidence = llm_conf
    else:
        # 1. Fallback Intent Detection via Keywords
        intent_keywords = {
        "TOTAL_VALUE": ["total", "value", "export"],
        "COUNT_PENDING": ["count", "how many", "pending"],
        "COUNT_SHIPMENTS": ["count", "how many", "shipment"],
        "TOP_N_CUSTOMERS": ["top", "customer", "buyer"],
        "STATUS_CHECK": ["status", "where", "shipment", "invoice"],
        "COMPLIANCE_ALERTS": ["compliance", "alert", "flag", "warning"],
        "ANOMALY_CHECK": ["anomaly", "suspicious", "fraud", "weird"],
        "DATE_FILTER": ["last", "this", "month", "week", "year", "before", "after", "between", "since"]
    }
    
    best_intent = "GENERAL"
    best_score = 0.0
    
        for potential_intent, kws in intent_keywords.items():
            matched = sum(1 for kw in kws if kw in query_lower)
            if matched > 0:
                score = matched / len(kws)
                if score > best_score:
                    best_score = score
                    best_intent = potential_intent
                    
        intent = best_intent
        confidence = round(best_score, 2)
    
    # Fast track overrides
    if "top" in query_lower and "customer" in query_lower:
        intent = "TOP_N_CUSTOMERS"
        confidence = 1.0
        
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
        def base_invoice_query():
            q = db_session.query(func.sum(Invoice.total_value))
            if user and user.role == 'trader':
                q = q.filter(Invoice.buyer == user.full_name)
            return q
            
        def base_invoice_count_query():
            q = db_session.query(func.count(Invoice.id))
            if user and user.role == 'trader':
                q = q.filter(Invoice.buyer == user.full_name)
            return q
            
        def base_shipment_count_query(status=None):
            q = db_session.query(func.count(Shipment.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == Shipment.invoice_no).filter(Invoice.buyer == user.full_name)
            if status:
                q = q.filter(Shipment.status == status)
            return q
            
        def base_compliance_count_query():
            q = db_session.query(func.count(ComplianceRecord.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == ComplianceRecord.shipment_id).filter(Invoice.buyer == user.full_name)
            return q
            
        def base_anomaly_count_query():
            q = db_session.query(func.count(AnomalyRecord.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == AnomalyRecord.record_id).filter(Invoice.buyer == user.full_name)
            return q

        if intent == "TOTAL_VALUE":
            date_filter = now.replace(day=1, hour=0, minute=0, second=0)
            if "last month" in query_lower:
                date_filter = now.replace(day=1) - relativedelta(months=1)
                sql_executed = "SELECT SUM(total_value) FROM invoices WHERE invoice_date >= date_trunc('month', NOW() - INTERVAL '1 month') AND invoice_date < date_trunc('month', NOW())"
                val = base_invoice_query().filter(
                    Invoice.invoice_date >= date_filter,
                    Invoice.invoice_date < now.replace(day=1)
                ).scalar() or 0
                answer = f"Total trade value last month was ₹{val:,.0f}"
            else:
                # default this month
                sql_executed = "SELECT SUM(total_value) FROM invoices WHERE invoice_date >= date_trunc('month', NOW())"
                val = base_invoice_query().filter(Invoice.invoice_date >= date_filter).scalar() or 0
                answer = f"Total trade value this month is ₹{val:,.0f}"
                
        elif intent == "COUNT_PENDING":
            sql_executed = "SELECT COUNT(*) FROM shipments WHERE status='pending'"
            val = base_shipment_count_query(status='pending').scalar() or 0
            answer = f"There are {val} pending shipments right now."
            
        elif intent == "COUNT_SHIPMENTS":
            sql_executed = "SELECT COUNT(*) FROM shipments"
            val = base_shipment_count_query().scalar() or 0
            answer = f"There are {val} total shipments in the system."

        elif intent == "DATE_FILTER":
            # Attempt to extract date range from entities or use defaults
            date_ent = entities.get("DATE", "")
            if "last month" in query_lower:
                date_filter_start = now.replace(day=1) - relativedelta(months=1)
                date_filter_end = now.replace(day=1)
                sql_executed = "SELECT SUM(total_value), COUNT(*) FROM invoices WHERE invoice_date >= prev_month_start AND invoice_date < this_month_start"
                val = base_invoice_query().filter(
                    Invoice.invoice_date >= date_filter_start,
                    Invoice.invoice_date < date_filter_end
                ).scalar() or 0
                cnt = base_invoice_count_query().filter(
                    Invoice.invoice_date >= date_filter_start,
                    Invoice.invoice_date < date_filter_end
                ).scalar() or 0
                answer = f"Last month: {cnt} invoices with total value ₹{val:,.0f}."
            elif "last week" in query_lower:
                date_filter_start = now - datetime.timedelta(days=7)
                sql_executed = "SELECT COUNT(*), SUM(total_value) FROM invoices WHERE invoice_date >= NOW() - INTERVAL '7 days'"
                val = base_invoice_query().filter(Invoice.invoice_date >= date_filter_start).scalar() or 0
                cnt = base_invoice_count_query().filter(Invoice.invoice_date >= date_filter_start).scalar() or 0
                answer = f"Last 7 days: {cnt} invoices totalling ₹{val:,.0f}."
            else:
                answer = f"Date filter query detected ('{date_ent}'). Try 'last month' or 'last week' for specific ranges."
                sql_executed = ""
            
        elif intent == "TOP_N_CUSTOMERS":
            limit = int(entities.get("CARDINAL", 5))
            sql_executed = f"SELECT buyer, SUM(total_value) as val FROM invoices GROUP BY buyer ORDER BY val DESC LIMIT {limit}"
            
            q = db_session.query(Invoice.buyer, func.sum(Invoice.total_value).label('val')).filter(Invoice.buyer.isnot(None))
            if user and user.role == 'trader':
                q = q.filter(Invoice.buyer == user.full_name)
                
            results = q.group_by(Invoice.buyer).order_by(func.sum(Invoice.total_value).desc()).limit(limit).all()
            
            data = [{"customer": r[0], "value": r[1]} for r in results]
            names_str = ", ".join([f"{i+1}. {r[0]} (₹{r[1]:,.0f})" for i, r in enumerate(results)])
            if user and user.role == 'trader':
                answer = f"Your total trade value: {names_str}"
            else:
                answer = f"Top {limit} customers by value: {names_str}"
            
        elif intent == "STATUS_CHECK" and "INVOICE_NO" in entities:
            inv = entities["INVOICE_NO"]
            sql_executed = f"SELECT * FROM shipments WHERE invoice_no ILIKE '%{inv}%'"
            
            q = db_session.query(Shipment).filter(Shipment.invoice_no.ilike(f"%{inv}%"))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == Shipment.invoice_no).filter(Invoice.buyer == user.full_name)
                
            shipment = q.first()
            if shipment:
                answer = f"Shipment {shipment.invoice_no}: status is {shipment.status.upper()}, loading at {shipment.port_of_loading}."
                data = [{"id": shipment.id, "status": shipment.status}]
            else:
                answer = f"Could not find an assigned shipment for invoice {inv}."
                
        elif intent == "COMPLIANCE_ALERTS":
            sql_executed = "SELECT COUNT(*) FROM compliance_records WHERE overall_status IN ('warning','critical')"
            val = base_compliance_count_query().filter(ComplianceRecord.overall_status.in_(['warning', 'critical'])).scalar() or 0
            answer = f"There are {val} active compliance alerts."
            
        elif intent == "ANOMALY_CHECK":
            sql_executed = "SELECT COUNT(*) FROM anomaly_records WHERE is_anomaly = true AND detected_at >= NOW() - INTERVAL '7 days'"
            date_filter = now - datetime.timedelta(days=7)
            val = base_anomaly_count_query().filter(AnomalyRecord.is_anomaly == True, AnomalyRecord.detected_at >= date_filter).scalar() or 0
            answer = f"{val} suspicious records detected in the last 7 days."
            
        else:
            answer = "I couldn't quite understand that. Try asking about 'pending shipments' or 'top customers'."
            
    except Exception as e:
        answer = f"Failed to execute query: {str(e)}"
        
    return {
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "sql_executed": sql_executed,
        "data": data,
        "record_count": len(data) if data else 0,
        "query_ms": int((time.time() - start) * 1000)
    }
