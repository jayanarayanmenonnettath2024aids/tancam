import os
import sys
from dotenv import load_dotenv
load_dotenv()
import json
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import SessionLocal, bulk_upsert
from db.models import Shipment, Invoice, TradeDocument, Customer, Product
from ingestion.erp_ingest import ingest_erp
from ingestion.excel_ingest import ingest_excel
from ingestion.pdf_ingest import extract_pdf_text_and_tables
from processing.transform import transform_erp_record
from processing.cleaner import clean_amount, clean_date
from processing.deduplicator import deduplicate_records
from processing.entity_resolver import resolve_customer, resolve_product

ERP_API_URL = os.getenv("ERP_API_URL", "http://127.0.0.1:8000/erp/transactions")
PORTAL_API_URL = os.getenv("PORTAL_API_URL", "http://127.0.0.1:8000/portal/shipments")

def run_pipeline(sources: list = None) -> dict:
    """
    Orchestrate all ingestors, clean/deduplicate/resolve data, save to DB.
    Returns a summary dict with counts per source and errors.
    """
    if sources is None:
        sources = ['erp', 'portal', 'excel', 'pdf']

    db = SessionLocal()
    summary = {
        "erp": 0,
        "portal": 0,
        "excel": 0,
        "pdf": 0,
        "email": 0,
        "duplicates_removed": 0,
        "errors": []
    }

    try:
        # ----- ERP -----
        if 'erp' in sources:
            try:
                raw_records = ingest_erp(ERP_API_URL)
                deduped = deduplicate_records(raw_records, unique_key="invoice_no")
                summary["duplicates_removed"] += len(raw_records) - len(deduped)

                shipments = []
                invoices = []
                for raw in deduped:
                    rec = transform_erp_record(raw)
                    shipments.append({
                        "id": rec["invoice_no"],
                        "invoice_no": rec["invoice_no"],
                        "quantity": rec["transaction"]["quantity"],
                        "unit_value": rec["transaction"]["unit_price"],
                        "total_value": rec["transaction"]["total_value"],
                        "shipment_date": clean_date(rec["transaction"]["transaction_date"]),
                        "source_system": "erp",
                        "port_of_loading": rec["shipment"]["origin_location"],
                        "port_of_discharge": rec["shipment"]["destination_location"],
                        "status": "pending"
                    })
                    invoices.append({
                        "invoice_no": rec["invoice_no"],
                        "shipment_id": rec["invoice_no"],
                        "buyer": resolve_customer(rec["customer"]["name"], db),
                        "total_value": rec["transaction"]["total_value"],
                        "source": "erp"
                    })

                bulk_upsert(db, Shipment, shipments, ['id'])
                bulk_upsert(db, Invoice, invoices, ['invoice_no'])
                summary["erp"] = len(shipments)
            except Exception as e:
                summary["errors"].append(f"ERP: {str(e)}")

        # ----- Portal -----
        if 'portal' in sources:
            try:
                import requests
                raw_data = requests.get(PORTAL_API_URL, timeout=10).json()
                deduped = deduplicate_records(raw_data, unique_key="invoice_no")
                summary["duplicates_removed"] += len(raw_data) - len(deduped)

                shipments = []
                for r in deduped:
                    shipments.append({
                        "id": r["invoice_no"],
                        "invoice_no": r["invoice_no"],
                        "shipping_bill_no": r.get("shipping_bill_no"),
                        "port_of_discharge": r.get("port"),
                        "clearance_status": r.get("clearance_status"),
                        "status": "cleared" if r.get("clearance_status") == "Cleared" else "pending",
                        "source_system": "portal"
                    })

                bulk_upsert(db, Shipment, shipments, ['id'])
                summary["portal"] = len(shipments)
            except Exception as e:
                summary["errors"].append(f"Portal: {str(e)}")

        # ----- Excel -----
        if 'excel' in sources:
            try:
                excel_paths = []
                sample_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_excel')
                if os.path.isdir(sample_dir):
                    excel_paths = [
                        os.path.join(sample_dir, f)
                        for f in os.listdir(sample_dir)
                        if f.endswith(('.xlsx', '.xls'))
                    ]

                rows_total = 0
                for fpath in excel_paths:
                    records = ingest_excel(fpath)
                    deduped = deduplicate_records(records, unique_key="invoice_no") if records else []
                    summary["duplicates_removed"] += len(records) - len(deduped)

                    docs = [{
                        "doc_type": "excel_row",
                        "source": "excel",
                        "extracted_json": row
                    } for row in deduped]

                    if docs:
                        db.bulk_insert_mappings(TradeDocument, docs)
                        db.commit()
                    rows_total += len(deduped)

                summary["excel"] = rows_total
            except Exception as e:
                summary["errors"].append(f"Excel: {str(e)}")

        # ----- PDF -----
        if 'pdf' in sources:
            try:
                pdf_paths = []
                sample_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_invoices')
                if os.path.isdir(sample_dir):
                    pdf_paths = [
                        os.path.join(sample_dir, f)
                        for f in os.listdir(sample_dir)
                        if f.endswith('.pdf')
                    ]

                for fpath in pdf_paths:
                    text, tables = extract_pdf_text_and_tables(fpath)
                    doc = TradeDocument(
                        doc_type="invoice",
                        source="pdf",
                        raw_content=text,
                        extracted_json={"tables": tables}
                    )
                    db.add(doc)

                db.commit()
                summary["pdf"] = len(pdf_paths)
            except Exception as e:
                summary["errors"].append(f"PDF: {str(e)}")

    finally:
        db.close()

    return summary
