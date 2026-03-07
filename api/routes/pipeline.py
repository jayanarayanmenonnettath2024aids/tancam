from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests
from db.database import SessionLocal
from db.models import TriggerLog

pipeline_bp = Blueprint('pipeline', __name__)
TRIGGER_URL = os.getenv("TRIGGER_SERVER_URL", "http://127.0.0.1:8001")

@pipeline_bp.route('/trigger/<source>', methods=['POST'])
@jwt_required()
def trigger_pipeline(source):
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).get(int(user_id))
        if not user or user.role != 'admin':
            return jsonify({"message": "Forbidden"}), 403
    finally:
        db.close()
        
    if source not in ['erp', 'portal', 'email', 'excel', 'pdf', 'run-all']:
        return jsonify({"message": "Invalid source"}), 400
        
    try:
        resp = requests.post(f"{TRIGGER_URL}/trigger/{source}", timeout=60)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.Timeout:
        return jsonify({"message": "Trigger timeout"}), 504
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@pipeline_bp.route('/status', methods=['GET'])
@jwt_required()
def get_pipeline_status():
    db = SessionLocal()
    try:
        # We can also fetch from the Trigger app
        try:
            resp = requests.get(f"{TRIGGER_URL}/trigger/status", timeout=5)
            if resp.status_code == 200:
                return jsonify(resp.json()), 200
        except:
            pass
            
        # Fallback to direct DB query if Trigger API is down
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
        
        return jsonify(status_list), 200
    finally:
        db.close()
        
@pipeline_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_pipeline_schedule():
    # Because apscheduler runs in the trigger app space safely
    # For now we'll mock the next runs relative to the current time since we don't have the API route in the trigger app
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    
    return jsonify([
        {"id": "job_erp", "next_run_time": (now + timedelta(minutes=5)).isoformat()},
        {"id": "job_portal", "next_run_time": (now + timedelta(minutes=10)).isoformat()},
        {"id": "job_email", "next_run_time": (now + timedelta(minutes=15)).isoformat()},
        {"id": "job_run_all", "next_run_time": (now + timedelta(minutes=30)).isoformat()}
    ]), 200
