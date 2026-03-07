from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.database import SessionLocal
from db.models import AnomalyRecord

anomalies_bp = Blueprint('anomalies', __name__)

@anomalies_bp.route('', methods=['GET'])
@anomalies_bp.route('/', methods=['GET'])
@jwt_required()
def get_anomalies():
    db = SessionLocal()
    try:
        min_score = request.args.get('min_score', type=float)
        
        query = db.query(AnomalyRecord).order_by(AnomalyRecord.anomaly_score.desc())
        
        if min_score is not None:
            query = query.filter(AnomalyRecord.anomaly_score >= min_score)
            
        results = query.all()
        payload = []
        for r in results:
            payload.append({
                "id": r.id,
                "record_type": r.record_type,
                "record_id": r.record_id,
                "anomaly_score": r.anomaly_score,
                "is_anomaly": r.is_anomaly,
                "description": r.description,
                "feature_values": r.feature_values,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None
            })
            
        return jsonify(payload), 200
    finally:
        db.close()

@anomalies_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect_anomalies():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).get(int(user_id))
        if not user or user.role != 'admin':
            return jsonify({"message": "Forbidden"}), 403
        from ml.anomaly_detector import detect_anomalies_in_db
        scanned, found = detect_anomalies_in_db(db)
        return jsonify({"scanned": scanned, "anomalies_found": found}), 200
    finally:
        db.close()
