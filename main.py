# main.py

from ingestion.erp_ingest import ingest_erp
from processing.transform import transform_erp_record
from ingestion.email_imap_ingest import ingest_unseen_emails
from ingestion.pdf_ingest import extract_pdf_text_and_tables
import requests

def main():

    # ---------------- ERP INGESTION ----------------
    erp_url = "http://127.0.0.1:8000/erp/transactions"
    erp_raw = ingest_erp(erp_url)

    print("\n========== ERP RAW DATA ==========")
    for record in erp_raw:
        print(record)

    print("\n========== ERP PROCESSED DATA ==========")
    for record in erp_raw:
        structured = transform_erp_record(record)
        print(structured)

    # ---------------- PORTAL INGESTION ----------------
    portal_url = "http://127.0.0.1:8000/portal/shipments"
    portal_raw = requests.get(portal_url).json()

    print("\n========== PORTAL RAW DATA ==========")
    for record in portal_raw:
        print(record)

    # ---------------- LINKING CHECK ----------------
    print("\n========== LINKING CHECK ==========")

    erp_invoices = {r["invoice_no"] for r in erp_raw}
    portal_invoices = {r["invoice_no"] for r in portal_raw}
    matching = erp_invoices.intersection(portal_invoices)

    print("ERP invoices:", erp_invoices)
    print("Portal invoices:", portal_invoices)
    print("Matching invoices:", matching)

    # ---------------- PDF EXTRACTION ----------------
    print("\n========== PDF EXTRACTION TEST ==========")

    pdf_path = "data/realistic_trade_invoice.pdf"
    text, tables = extract_pdf_text_and_tables(pdf_path)

    print("\n--- Extracted Text ---\n")
    print(text)

    print("\n--- Extracted Tables ---\n")
    for table in tables:
        for row in table:
            print(row)
        print("\n")

    # ---------------- IMAP EMAIL INGESTION ----------------
    print("\n========== IMAP EMAIL TEST ==========")

    USERNAME = "novacore.projects2025@gmail.com"
    APP_PASSWORD = "rknfdktpyqffkxiq"

    try:
        invoices = ingest_unseen_emails(USERNAME, APP_PASSWORD)
        
        for inv in invoices:
            print(inv)

    except Exception as e:
        print("Email connection failed:", str(e))


if __name__ == "__main__":
    main()