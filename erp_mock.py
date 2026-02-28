from fastapi import FastAPI

app = FastAPI()

@app.get("/erp/transactions")
def get_transactions():
    return [
        {
            "invoice_no": "INV1001",
            "client_name": "ABC Textiles Pvt Ltd",
            "gst_id": "33ABCDE1234F1Z5",
            "item": "Cotton Yarn",
            "category": "Textile",
            "hs_code": None,
            "qty": 850,
            "rate": 130,
            "date": "2026-03-28",
            "trade_type": "DOMESTIC",
            "origin": "Coimbatore",
            "destination": "Chennai",
            "port": None,
            "customs_duty": None
        },
        {
            "invoice_no": "INV2001",
            "client_name": "Global Knit Exports",
            "gst_id": "33KNIT5566F1Z5",
            "item": "T-Shirts",
            "category": "Apparel",
            "hs_code": "6109",
            "qty": 600,
            "rate": 400,
            "date": "2026-03-29",
            "trade_type": "EXPORT",
            "origin": "Tiruppur",
            "destination": "USA",
            "port": "Chennai Port",
            "customs_duty": 14000
        }
    ]

@app.get("/portal/shipments")
def get_portal_shipments():
    return [
        {
            "invoice_no": "INV2001",
            "shipping_bill_no": "SB9001",
            "port": "Chennai Port",
            "clearance_status": "Cleared",
            "clearance_date": "2026-03-30"
        }
    ]