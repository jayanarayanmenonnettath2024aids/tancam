import bcrypt
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from db.database import SessionLocal
from db.models import User, TokenBlacklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing email or password"}), 400
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data['email']).first()
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.hashed_password.encode('utf-8')):
            return jsonify({"message": "Invalid email or password"}), 401
            
        user.last_login = datetime.utcnow()
        db.commit()
        
        user_info = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_info
        }), 200
    finally:
        db.close()

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=str(user_id))
    return jsonify(access_token=new_access_token), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db = SessionLocal()
    try:
        db.add(TokenBlacklist(jti=jti))
        db.commit()
        return jsonify({"message": "logged out"}), 200
    finally:
        db.close()

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        user = db.query(User).get(int(user_id))
        if not user:
             return jsonify({"message": "User not found"}), 404
        user_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
        return jsonify(user_data), 200
    finally:
        db.close()
