from flask import Blueprint, jsonify, Response, stream_with_context, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract, or_, and_
from db.database import SessionLocal
from db.models import Invoice, Shipment, ComplianceRecord, AnomalyRecord, TradeDocument, Customer, Product
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import time

analytics_bp = Blueprint('analytics', __name__)

def get_summary_data(user=None):
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_prev_month = (first_day_this_month - relativedelta(months=1))
        
        def base_invoice_query():
            q = db.query(func.sum(Invoice.total_value))
            if user and user.role == 'trader':
                q = q.filter(Invoice.buyer == user.full_name)
            return q
            
        def base_invoice_buyer_query():
            q = db.query(Invoice.buyer, func.sum(Invoice.total_value).label('val'))
            if user and user.role == 'trader':
                q = q.filter(Invoice.buyer == user.full_name)
            return q
            
        def base_shipment_query():
            q = db.query(func.count(Shipment.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == Shipment.invoice_no).filter(Invoice.buyer == user.full_name)
            return q
            
        def base_compliance_query():
            q = db.query(func.count(ComplianceRecord.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == ComplianceRecord.shipment_id).filter(Invoice.buyer == user.full_name)
            return q
            
        def base_anomaly_query():
            q = db.query(func.count(AnomalyRecord.id))
            if user and user.role == 'trader':
                q = q.join(Invoice, Invoice.shipment_id == AnomalyRecord.record_id).filter(Invoice.buyer == user.full_name)
            return q

        # total_trade_value_month
        this_month_val = base_invoice_query().filter(
            or_(Invoice.invoice_date >= first_day_this_month, Invoice.invoice_date == None)
        ).scalar() or 0
        
        # total_trade_value_prev_month
        prev_month_val = base_invoice_query().filter(
            or_(
                and_(Invoice.invoice_date >= first_day_prev_month, Invoice.invoice_date < first_day_this_month),
                Invoice.invoice_date == None
            )
        ).scalar() or 0
        
        # Feature Engineering: MoM Growth
        if prev_month_val > 0:
            mom_growth = ((this_month_val - prev_month_val) / prev_month_val) * 100
        else:
            mom_growth = 100.0 if this_month_val > 0 else 0.0
        
        # active_shipments
        active_shipments = base_shipment_query().filter(Shipment.status == 'pending').scalar() or 0
        
        # compliance_rate
        total_compliance = base_compliance_query().scalar() or 0
        ok_compliance = base_compliance_query().filter(ComplianceRecord.overall_status == 'ok').scalar() or 0
        compliance_rate = (ok_compliance / total_compliance * 100) if total_compliance > 0 else 100
        
        # anomalies_detected
        anomalies_detected = base_anomaly_query().filter(AnomalyRecord.is_anomaly == True).scalar() or 0
        
        # docs_processed (Global metric)
        docs_processed = db.query(func.count(TradeDocument.id)).scalar() or 0
        
        # top_5_customers
        top_customers = base_invoice_buyer_query().filter(Invoice.buyer.isnot(None)).group_by(Invoice.buyer).order_by(func.sum(Invoice.total_value).desc()).limit(5).all()
        top_5_customers = [{"name": c[0], "value": c[1]} for c in top_customers]
        
        # Feature Engineering: Risk Concentration & Revenue Share
        global_val = db.query(func.sum(Invoice.total_value)).filter(
            or_(Invoice.invoice_date >= first_day_this_month, Invoice.invoice_date == None)
        ).scalar() or 0
        
        risk_concentration = 0.0
        share_of_revenue = 0.0
        if user and user.role == 'trader':
            share_of_revenue = (this_month_val / global_val * 100) if global_val > 0 else 0.0
        else:
            top_3_val = sum(c[1] for c in top_customers[:3])
            risk_concentration = (top_3_val / this_month_val * 100) if this_month_val > 0 else 0.0
        
        # top_5_products (Now repurposed as Destination Ports)
        q_ports = db.query(
            Shipment.port_of_discharge,
            func.count(Shipment.id).label('count')
        )
        if user and user.role == 'trader':
            q_ports = q_ports.join(Invoice, Invoice.shipment_id == Shipment.invoice_no).filter(Invoice.buyer == user.full_name)
            
        top_ports = q_ports.filter(Shipment.port_of_discharge.isnot(None)).group_by(Shipment.port_of_discharge).order_by(func.count(Shipment.id).desc()).limit(5).all()
        top_5_products = [{"name": p[0], "count": p[1]} for p in top_ports]
        
        # source_breakdown (Global)
        sources = db.query(
            TradeDocument.source,
            func.count(TradeDocument.id)
        ).group_by(TradeDocument.source).all()
        source_breakdown = {s[0]: s[1] for s in sources if s[0]}
        
        return {
            "total_trade_value_month": this_month_val,
            "total_trade_value_prev_month": prev_month_val,
            "mom_growth_pct": round(mom_growth, 1),
            "risk_concentration_pct": round(risk_concentration, 1),
            "share_of_revenue_pct": round(share_of_revenue, 1),
            "active_shipments": active_shipments,
            "compliance_rate": round(compliance_rate, 1),
            "anomalies_detected": anomalies_detected,
            "docs_processed": docs_processed,
            "top_5_customers": top_5_customers,
            "top_5_products": top_5_products,
            "source_breakdown": source_breakdown
        }
    finally:
        db.close()

@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    db = SessionLocal()
    from db.models import User
    user = db.query(User).get(int(user_id))
    db.close()
    return jsonify(get_summary_data(user)), 200

@analytics_bp.route('/stream', methods=['GET'])
def stream_summary():
    # Wait for the token inside query params to bypass default headers requirement
    token_str = request.args.get('token')
    if not token_str:
        return jsonify({"message": "Missing token"}), 401
    from flask_jwt_extended import decode_token
    from db.models import User
    
    try:
        decoded = decode_token(token_str)
        user_id = decoded.get("sub")
        db = SessionLocal()
        user = db.query(User).get(int(user_id))
        db.close()
    except Exception:
        user = None
        
    def generate():
        while True:
            data = get_summary_data(user)
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(10)  # push every 10 seconds
            
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    db = SessionLocal()
    try:
        # Group by month for sqlite and postgres compat
        # Sqlite doesn't have date_trunc. We'll extract formatted string
        dialect = db.bind.dialect.name
        
        if dialect == 'sqlite':
            results = db.query(
                func.strftime('%Y-%m', Invoice.invoice_date).label('month'),
                func.sum(Invoice.total_value),
                func.count(Invoice.id)
            ).filter(Invoice.invoice_date.isnot(None)).group_by('month').order_by('month').all()
        else:
            results = db.query(
                func.to_char(func.date_trunc('month', Invoice.invoice_date), 'YYYY-MM').label('month'),
                func.sum(Invoice.total_value),
                func.count(Invoice.id)
            ).filter(Invoice.invoice_date.isnot(None)).group_by('month').order_by('month').all()
            
        trends = [{"month": r[0], "value": r[1] or 0, "volume": r[2]} for r in results if r[0]]
        
        # Limit to last 12
        return jsonify(trends[-12:]), 200
    finally:
        db.close()

@analytics_bp.route('/source-split', methods=['GET'])
@jwt_required()
def get_source_split():
    db = SessionLocal()
    try:
        sources = db.query(
            TradeDocument.source,
            func.count(TradeDocument.id)
        ).group_by(TradeDocument.source).all()
        
        total = sum(s[1] for s in sources)
        result = []
        for s in sources:
            if s[0]:
                pct = (s[1] / total * 100) if total > 0 else 0
                result.append({"source": s[0], "count": s[1], "percentage": round(pct, 1)})
                
        return jsonify(result), 200
    finally:
        db.close()

@analytics_bp.route('/compliance-trend', methods=['GET'])
@jwt_required()
def get_compliance_trend():
    db = SessionLocal()
    try:
        dialect = db.bind.dialect.name
        from db.models import ComplianceRecord

        if dialect == 'sqlite':
            results = db.query(
                func.strftime('%Y-%m', ComplianceRecord.checked_at).label('month'),
                func.count(ComplianceRecord.id).label('total'),
                func.sum(
                    func.case((ComplianceRecord.overall_status == 'ok', 1), else_=0)
                ).label('ok_count')
            ).filter(ComplianceRecord.checked_at.isnot(None)).group_by('month').order_by('month').all()
        else:
            results = db.query(
                func.to_char(func.date_trunc('month', ComplianceRecord.checked_at), 'YYYY-MM').label('month'),
                func.count(ComplianceRecord.id).label('total'),
                func.sum(
                    func.case((ComplianceRecord.overall_status == 'ok', 1), else_=0)
                ).label('ok_count')
            ).filter(ComplianceRecord.checked_at.isnot(None)).group_by('month').order_by('month').all()

        trend = []
        for r in results:
            if r[0]:
                total = r[1] or 0
                ok = int(r[2] or 0)
                rate = round((ok / total * 100), 1) if total > 0 else 100.0
                trend.append({"month": r[0], "total": total, "ok": ok, "compliance_rate": rate})

        return jsonify(trend[-12:]), 200
    finally:
        db.close()
