import time
import os
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from db.database import get_session, bulk_upsert
from db.models import TriggerLog, Shipment, Invoice, TradeDocument, Customer, Product
from ingestion.erp_ingest import ingest_erp
from processing.transform import transform_erp_record
from ingestion.email_imap_ingest import ingest_unseen_emails
from ingestion.excel_ingest import ingest_excel
from ingestion.pdf_ingest import extract_pdf_text_and_tables

app = FastAPI(title="UnifyOps Trigger API")

ERP_API_URL = os.getenv("ERP_API_URL", "http://127.0.0.1:8000/erp/transactions")
PORTAL_API_URL = os.getenv("PORTAL_API_URL", "http://127.0.0.1:8000/portal/shipments")
GMAIL_USER = os.getenv("GMAIL_USER", "dummy@gmail.com")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "dummy")

def log_trigger(session, source: str, records_affected: int, status: str, duration_ms: int, error_message: str = None):
    log = TriggerLog(
        source=source,
        records_affected=records_affected,
        status=status,
        duration_ms=duration_ms,
        error_message=error_message
    )
    session.add(log)
    session.commit()

@app.post("/trigger/erp")
def trigger_erp():
    start_time = time.time()
    db = next(get_session())
    try:
        raw_data = ingest_erp(ERP_API_URL)
        processed_records = [transform_erp_record(r) for r in raw_data]
        
        # We need to map dict structure to DB schemas and bulk upsert
        shipments = []
        invoices = []
        for r in processed_records:
            shipments.append({
                "id": r["invoice_no"],
                "invoice_no": r["invoice_no"],
                "quantity": r["transaction"]["quantity"],
                "unit_value": r["transaction"]["unit_price"],
                "total_value": r["transaction"]["total_value"],
                "shipment_date": datetime.strptime(r["transaction"]["transaction_date"], "%Y-%m-%d"),
                "source_system": "erp",
                "port_of_loading": r["shipment"]["origin_location"],
                "port_of_discharge": r["shipment"]["destination_location"],
                "status": "pending"
            })
            invoices.append({
                "invoice_no": r["invoice_no"],
                "shipment_id": r["invoice_no"],
                "buyer": r["customer"]["name"],
                "total_value": r["transaction"]["total_value"],
                "source": "erp"
            })
            
        bulk_upsert(db, Shipment, shipments, ['id'])
        bulk_upsert(db, Invoice, invoices, ['invoice_no'])
        
        from compliance.compliance_runner import run_compliance_check
        for s in shipments:
            try: run_compliance_check(s["id"], db)
            except: pass
        
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "erp", len(shipments), "ok", duration)
        
        return {
            "status": "ok",
            "records_inserted": len(shipments),
            "duration_ms": duration,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "erp", 0, "failed", duration, str(e))
        return {"status": "error", "message": str(e)}

@app.post("/trigger/portal")
def trigger_portal():
    start_time = time.time()
    db = next(get_session())
    try:
        raw_data = requests.get(PORTAL_API_URL).json()
        shipments = []
        for r in raw_data:
            clearance_date = None
            if r.get("clearance_date"):
                try: clearance_date = datetime.strptime(r["clearance_date"], "%Y-%m-%d")
                except: pass
                
            shipments.append({
                "id": r["invoice_no"],  # Assuming ID matches invoice_no per our schema design
                "invoice_no": r["invoice_no"],
                "shipping_bill_no": r["shipping_bill_no"],
                "port_of_discharge": r["port"],
                "clearance_status": r["clearance_status"],
                "status": "cleared" if r.get("clearance_status") == "Cleared" else "pending",
                "updated_at": datetime.now(timezone.utc)
            })
            
        bulk_upsert(db, Shipment, shipments, ['id'])
        
        from compliance.compliance_runner import run_compliance_check
        for s in shipments:
            try: run_compliance_check(s["id"], db)
            except: pass
        
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "portal", len(shipments), "ok", duration)
        
        return {"status": "ok", "shipments_upserted": len(shipments)}
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "portal", 0, "failed", duration, str(e))
        return {"status": "error", "message": str(e)}

@app.post("/trigger/email")
def trigger_email():
    start_time = time.time()
    db = next(get_session())
    try:
        invoices_data = ingest_unseen_emails(GMAIL_USER, GMAIL_PASSWORD)
        docs = []
        invoices = []
        for inv in invoices_data:
            docs.append({
                "doc_type": "email",
                "source": "email",
                "extracted_json": inv,
            })
            if "invoice_no" in inv:
                invoices.append({
                    "invoice_no": inv["invoice_no"],
                    "buyer": inv.get("client_name"),
                    "total_value": float(inv["amount"]) if inv.get("amount") else None,
                    "source": "email"
                })
        
        if docs:
            db.bulk_insert_mappings(TradeDocument, docs)
            db.commit()
            
        if invoices:
            bulk_upsert(db, Invoice, invoices, ['invoice_no'])
            
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "email", len(invoices_data), "ok", duration)
        
        return {
            "status": "ok",
            "emails_processed": len(invoices_data),
            "invoices_extracted": len(invoices)
        }
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "email", 0, "failed", duration, str(e))
        return {"status": "error", "message": str(e)}

@app.post("/trigger/excel")
async def trigger_excel(file: UploadFile = None):
    start_time = time.time()
    db = next(get_session())
    try:
        file_path = "data/sample_excel.xlsx"
        if file:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
                
        records = []
        if os.path.exists(file_path):
            records = ingest_excel(file_path)
            
        docs = []
        for row in records:
            docs.append({
                "doc_type": "excel_row",
                "source": "excel",
                "extracted_json": row
            })
        
        if docs:
            db.bulk_insert_mappings(TradeDocument, docs)
            db.commit()
            
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "excel", len(records), "ok", duration)
            
        return {"status": "ok", "rows_inserted": len(records)}
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "excel", 0, "failed", duration, str(e))
        return {"status": "error", "message": str(e)}

@app.post("/trigger/pdf")
async def trigger_pdf(file: UploadFile = None):
    start_time = time.time()
    db = next(get_session())
    try:
        file_path = "data/sample_invoice.pdf"
        if file:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
                
        text = ""
        tables = []
        if os.path.exists(file_path):
            text, tables = extract_pdf_text_and_tables(file_path)
            
        doc = TradeDocument(
            doc_type="invoice",
            source="pdf",
            raw_content=text,
            extracted_json={"tables": tables}
        )
        db.add(doc)
        db.commit()
        
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "pdf", 1, "ok", duration)
        
        return {"status": "ok", "invoices_extracted": 1}
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_trigger(db, "pdf", 0, "failed", duration, str(e))
        return {"status": "error", "message": str(e)}

@app.post("/trigger/run-all")
def trigger_run_all():
    start = time.time()
    r_erp = trigger_erp()
    r_portal = trigger_portal()
    # We swallow errors on email if missing credentials
    try: r_email = trigger_email()
    except: r_email = {"status": "error"}
    
    import asyncio
    try: r_excel = asyncio.run(trigger_excel(None))
    except: r_excel = {"status": "error"}
    
    try: r_pdf = asyncio.run(trigger_pdf(None))
    except: r_pdf = {"status": "error"}
    
    return {
        "erp": r_erp,
        "portal": r_portal,
        "email": r_email,
        "excel": r_excel,
        "pdf": r_pdf,
        "total_duration_ms": int((time.time() - start) * 1000),
        "triggered_at": datetime.now(timezone.utc).isoformat()
    }

@app.get("/trigger/status")
def trigger_status():
    db = next(get_session())
    sources = ["erp", "portal", "email", "excel", "pdf", "run-all"]
    status_list = []
    
    for s in sources:
        log = db.query(TriggerLog).filter(TriggerLog.source == s).order_by(TriggerLog.triggered_at.desc()).first()
        if log:
            status_list.append({
                "source": log.source,
                "triggered_at": log.triggered_at.isoformat(),
                "records_affected": log.records_affected,
                "status": log.status,
                "duration_ms": log.duration_ms
            })
        else:
            status_list.append({"source": s, "status": "never_run"})
            
    return status_list
