from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db.database import SessionLocal

query_bp = Blueprint('query', __name__)

@query_bp.route('', methods=['POST'])
@query_bp.route('/', methods=['POST'])
@jwt_required()
def handle_query():
    data = request.get_json()
    if not data or not data.get('query'):
        return jsonify({"message": "Query text required"}), 400
        
    db = SessionLocal()
    try:
        user_id = get_jwt_identity()
        from db.models import User
        user = db.query(User).get(int(user_id))
        
        from ml.nlp_query import process_query
        result = process_query(data['query'], db, user=user)
        
        if result.get("intent") == "GENERAL" or result.get("confidence", 0.0) < 0.3:
            return jsonify({
                "answer": "I can answer questions like: 'total export value this month', 'top 5 customers by value', 'how many pending shipments', 'any GST compliance alerts', 'suspicious invoices last week'",
                "intent": "GENERAL",
                "confidence": result.get("confidence", 0.0),
                "suggestions": [
                    "total export value this month",
                    "top 5 customers by value", 
                    "how many pending shipments",
                    "any GST compliance alerts",
                    "suspicious invoices last week"
                ],
                "data": []
            }), 200
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()
