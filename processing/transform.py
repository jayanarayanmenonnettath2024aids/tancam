def transform_erp_record(raw):
    quantity = int(raw["qty"])
    unit_price = float(raw["rate"])

    processed = {
        "invoice_no": raw["invoice_no"],

        "customer": {
            "name": raw["client_name"],
            "gst_number": raw["gst_id"],
            "country": "India"
        },
        "product": {
            "name": raw["item"],
            "category": raw["category"],
            "hs_code": raw["hs_code"]
        },
        "transaction": {
            "quantity": quantity,
            "unit_price": unit_price,
            "total_value": quantity * unit_price,
            "transaction_date": raw["date"],
            "trade_type": raw["trade_type"]
        },
        "shipment": {
            "origin_location": raw["origin"],
            "destination_location": raw["destination"],
            "port": raw["port"],
            "customs_duty": raw["customs_duty"]
        }
    }

    return processed