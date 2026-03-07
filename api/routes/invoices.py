from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os
from db.database import SessionLocal
from db.models import Invoice

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/', methods=['GET'])
@jwt_required()
def get_invoices():
    db = SessionLocal()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        source = request.args.get('source')
        
        query = db.query(Invoice)
        
        if source:
            query = query.filter(Invoice.source == source)
            
        total_count = query.count()
        invoices = query.order_by(Invoice.extracted_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        result = []
        for inv in invoices:
            result.append({
                "id": inv.id,
                "invoice_no": inv.invoice_no,
                "shipment_id": inv.shipment_id,
                "buyer": inv.buyer,
                "seller": inv.seller,
                "total_value": inv.total_value,
                "gst_amount": inv.gst_amount,
                "currency": inv.currency,
                "source": inv.source,
                "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            })
            
        return jsonify({
            "items": result,
            "total": total_count,
            "page": page,
            "pages": (total_count + per_page - 1) // per_page
        }), 200
    finally:
        db.close()

@invoices_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_invoice():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).get(int(user_id))
        if not user or user.role not in ['admin', 'analyst']:
            return jsonify({"message": "Forbidden"}), 403
    finally:
        db.close()
        
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
        
    # Proxy to FastAPI trigger server
    TRIGGER_URL = os.getenv("TRIGGER_SERVER_URL", "http://127.0.0.1:8001")
    target = None
    if file.filename.endswith('.pdf'):
        target = f"{TRIGGER_URL}/trigger/pdf"
    elif file.filename.endswith(('.xlsx', '.xls')):
        target = f"{TRIGGER_URL}/trigger/excel"
    else:
        return jsonify({"message": "Unsupported file format"}), 400
        
    try:
        # Read file contents and forward it via multipart/form-data
        files = {'file': (file.filename, file.read(), file.content_type)}
        resp = requests.post(target, files=files)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"message": f"Trigger server communication failed: {str(e)}"}), 500
