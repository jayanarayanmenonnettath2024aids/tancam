from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db.database import SessionLocal

query_bp = Blueprint('query', __name__)

@query_bp.route('/', methods=['POST'])
@jwt_required()
def handle_query():
    data = request.get_json()
    if not data or not data.get('query'):
        return jsonify({"message": "Query text required"}), 400
        
    db = SessionLocal()
    try:
        from ml.nlp_query import process_query
        result = process_query(data['query'], db)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()
