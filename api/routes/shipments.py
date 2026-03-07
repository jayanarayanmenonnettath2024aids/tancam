from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.database import SessionLocal
from db.models import Shipment, Invoice, ComplianceRecord, AnomalyRecord

shipments_bp = Blueprint('shipments', __name__)

@shipments_bp.route('/', methods=['GET'])
@jwt_required()
def get_shipments():
    db = SessionLocal()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        source_system = request.args.get('source_system')
        search = request.args.get('search')
        
        query = db.query(Shipment)
        
        if status:
            query = query.filter(Shipment.status == status)
        if source_system:
            query = query.filter(Shipment.source_system == source_system)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(Shipment.invoice_no.ilike(search_pattern))
            
        total_count = query.count()
        shipments = query.order_by(Shipment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        result = []
        for s in shipments:
            result.append({
                "id": s.id,
                "invoice_no": s.invoice_no,
                "quantity": s.quantity,
                "total_value": s.total_value,
                "currency": s.currency,
                "shipment_date": s.shipment_date.isoformat() if s.shipment_date else None,
                "status": s.status,
                "source_system": s.source_system,
                "port_of_loading": s.port_of_loading,
                "port_of_discharge": s.port_of_discharge,
                "shipping_bill_no": s.shipping_bill_no,
                "clearance_status": s.clearance_status
            })
            
        return jsonify({
            "items": result,
            "total": total_count,
            "page": page,
            "pages": (total_count + per_page - 1) // per_page
        }), 200
    finally:
        db.close()

@shipments_bp.route('/<shipment_id>', methods=['GET'])
@jwt_required()
def get_shipment(shipment_id):
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return jsonify({"message": "Shipment not found"}), 404
            
        invoice = db.query(Invoice).filter(Invoice.shipment_id == shipment_id).first()
        compliance = db.query(ComplianceRecord).filter(ComplianceRecord.shipment_id == shipment_id).first()
        anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.record_type == 'shipment', AnomalyRecord.record_id == shipment_id).first()
        
        response = {
            "shipment": {
                "id": shipment.id,
                "invoice_no": shipment.invoice_no,
                "quantity": shipment.quantity,
                "total_value": shipment.total_value,
                "currency": shipment.currency,
                "shipment_date": shipment.shipment_date.isoformat() if shipment.shipment_date else None,
                "status": shipment.status,
                "source_system": shipment.source_system,
            },
            "invoice": None,
            "compliance": None,
            "anomaly_flag": anomaly.is_anomaly if anomaly else False
        }
        
        if invoice:
            response["invoice"] = {
                "buyer": invoice.buyer,
                "seller": invoice.seller,
                "total_value": invoice.total_value,
            }
        
        if compliance:
            response["compliance"] = {
                "overall_status": compliance.overall_status,
                "gstin_valid": compliance.gstin_valid,
                "checked_at": compliance.checked_at.isoformat() if compliance.checked_at else None
            }
            
        return jsonify(response), 200
    finally:
        db.close()

@shipments_bp.route('/<shipment_id>', methods=['PATCH'])
@jwt_required()
def update_shipment(shipment_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({"message": "New status required"}), 400
        
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).get(int(user_id))
        if not user or user.role not in ['admin', 'analyst']:
            return jsonify({"message": "Forbidden"}), 403
        
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return jsonify({"message": "Shipment not found"}), 404
            
        shipment.status = new_status
        db.commit()
        return jsonify({"message": "Shipment updated", "status": shipment.status}), 200
    finally:
        db.close()
