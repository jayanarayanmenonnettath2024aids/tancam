import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from db.database import SessionLocal
from db.models import TokenBlacklist

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # CORS setup
    FRONTEND_URL = os.getenv('REACT_APP_API_URL', 'http://localhost:3000') # Or vercel URL mapping
    # Allow local and deployed frontend
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", FRONTEND_URL, "https://unifyops.vercel.app"]}})
    
    jwt = JWTManager(app)
    
    # Blocklist loader
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        db = SessionLocal()
        try:
            token = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
            return token is not None
        finally:
            db.close()
            
    # Register blueprints
    from api.routes.auth import auth_bp
    from api.routes.shipments import shipments_bp
    from api.routes.invoices import invoices_bp
    from api.routes.compliance import compliance_bp
    from api.routes.analytics import analytics_bp
    from api.routes.anomalies import anomalies_bp
    from api.routes.query import query_bp
    from api.routes.pipeline import pipeline_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(shipments_bp, url_prefix='/api/shipments')
    app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    app.register_blueprint(compliance_bp, url_prefix='/api/compliance')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(anomalies_bp, url_prefix='/api/anomalies')
    app.register_blueprint(query_bp, url_prefix='/api/query')
    app.register_blueprint(pipeline_bp, url_prefix='/api/pipeline')
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        return jsonify(error=str(e)), 500
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5000, debug=True)
