from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract, or_, and_
from db.database import SessionLocal
from db.models import Invoice, Shipment, ComplianceRecord, AnomalyRecord, TradeDocument, Customer, Product
from datetime import datetime
from dateutil.relativedelta import relativedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_prev_month = (first_day_this_month - relativedelta(months=1))
        
        # total_trade_value_month
        this_month_val = db.query(func.sum(Invoice.total_value)).filter(
            or_(Invoice.invoice_date >= first_day_this_month, Invoice.invoice_date == None)
        ).scalar() or 0
        
        # total_trade_value_prev_month
        prev_month_val = db.query(func.sum(Invoice.total_value)).filter(
            or_(
                and_(Invoice.invoice_date >= first_day_prev_month, Invoice.invoice_date < first_day_this_month),
                Invoice.invoice_date == None
            )
        ).scalar() or 0
        
        # active_shipments
        active_shipments = db.query(func.count(Shipment.id)).filter(Shipment.status == 'pending').scalar() or 0
        
        # compliance_rate
        total_compliance = db.query(func.count(ComplianceRecord.id)).scalar() or 0
        ok_compliance = db.query(func.count(ComplianceRecord.id)).filter(ComplianceRecord.overall_status == 'ok').scalar() or 0
        compliance_rate = (ok_compliance / total_compliance * 100) if total_compliance > 0 else 100
        
        # anomalies_detected
        anomalies_detected = db.query(func.count(AnomalyRecord.id)).filter(AnomalyRecord.is_anomaly == True).scalar() or 0
        
        # docs_processed
        docs_processed = db.query(func.count(TradeDocument.id)).scalar() or 0
        
        # top_5_customers
        top_customers = db.query(
            Invoice.buyer, 
            func.sum(Invoice.total_value).label('val')
        ).filter(Invoice.buyer.isnot(None)).group_by(Invoice.buyer).order_by(func.sum(Invoice.total_value).desc()).limit(5).all()
        top_5_customers = [{"name": c[0], "value": c[1]} for c in top_customers]
        
        # top_5_products 
        top_products = db.query(
            Product.canonical_name,
            func.count(Shipment.id).label('count')
        ).join(Shipment, Shipment.product_id == Product.master_id).group_by(Product.canonical_name).order_by(func.count(Shipment.id).desc()).limit(5).all()
        top_5_products = [{"name": p[0], "count": p[1]} for p in top_products]
        
        # source_breakdown
        sources = db.query(
            TradeDocument.source,
            func.count(TradeDocument.id)
        ).group_by(TradeDocument.source).all()
        source_breakdown = {s[0]: s[1] for s in sources if s[0]}
        
        return jsonify({
            "total_trade_value_month": this_month_val,
            "total_trade_value_prev_month": prev_month_val,
            "active_shipments": active_shipments,
            "compliance_rate": round(compliance_rate, 1),
            "anomalies_detected": anomalies_detected,
            "docs_processed": docs_processed,
            "top_5_customers": top_5_customers,
            "top_5_products": top_5_products,
            "source_breakdown": source_breakdown
        }), 200
    finally:
        db.close()

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
