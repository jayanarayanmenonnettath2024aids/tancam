from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.database import SessionLocal
from db.models import ComplianceRecord, Shipment, Invoice

compliance_bp = Blueprint('compliance', __name__)

@compliance_bp.route('', methods=['GET'])
@compliance_bp.route('/', methods=['GET'])
@jwt_required()
def get_compliance():
    db = SessionLocal()
    try:
        overall_status = request.args.get('status')
        source = request.args.get('source')
        
        query = db.query(ComplianceRecord).join(Shipment)
        
        if overall_status:
            query = query.filter(ComplianceRecord.overall_status == overall_status)
        if source:
            query = query.filter(Shipment.source_system == source)
            
        records = query.order_by(ComplianceRecord.checked_at.desc()).all()
        
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "shipment_id": r.shipment_id,
                "overall_status": r.overall_status,
                "gstin_valid": r.gstin_valid,
                "hs_code_valid": r.hs_code_valid,
                "gst_amount_valid": r.gst_amount_valid,
                "missing_docs": r.missing_docs,
                "checked_at": r.checked_at.isoformat() if r.checked_at else None
            })
            
        return jsonify(result), 200
    finally:
        db.close()

@compliance_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    db = SessionLocal()
    try:
        # Fetch only warning or critical
        records = db.query(ComplianceRecord).filter(
            ComplianceRecord.overall_status.in_(['warning', 'critical'])
        ).order_by(
            ComplianceRecord.overall_status.desc(), 
            ComplianceRecord.checked_at.desc()
        ).all()
        
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "shipment_id": r.shipment_id,
                "overall_status": r.overall_status,
                "gstin_flag": r.gstin_flag,
                "hs_code_flag": r.hs_code_flag,
                "gst_amount_flag": r.gst_amount_flag,
                "missing_docs": r.missing_docs,
                "checked_at": r.checked_at.isoformat() if r.checked_at else None
            })
            
        return jsonify(result), 200
    finally:
        db.close()

@compliance_bp.route('/run', methods=['POST'])
@jwt_required()
def run_compliance():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).get(int(user_id))
        if not user or user.role != 'admin':
            return jsonify({"message": "Forbidden"}), 403
        # Find shipments missing a compliance record
        subquery = db.query(ComplianceRecord.shipment_id)
        shipments = db.query(Shipment).filter(Shipment.id.notin_(subquery)).all()
        
        if not shipments:
            return jsonify({"checked": 0, "ok": 0, "warning": 0, "critical": 0}), 200
            
        # We will implement the actual runner logic in compliance_runner.py
        # Here we just import and call it
        from compliance.compliance_runner import run_compliance_check
        
        results = {"checked": 0, "ok": 0, "warning": 0, "critical": 0}
        
        for s in shipments:
            record = run_compliance_check(s.id, db)
            if record:
                results["checked"] += 1
                results[record.overall_status] += 1
                
        return jsonify(results), 200
    finally:
        db.close()
