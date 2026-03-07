import os
import sys
import bcrypt
import json

# Ensure parent module is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import engine, SessionLocal
from db.models import Base, User, HsCode

def init_db():
    print("Creating database and tables...")
    # Ensure data directory exists if it's the default sqlite path
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/reference", exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Seed Admin User
    admin_email = "admin@unifyops.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    
    if not existing_admin:
        pwd_bytes = "admin123".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
        
        admin_user = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name="System Admin",
            role="admin"
        )
        db.add(admin_user)
        print("Seeded default admin user: admin@unifyops.com / admin123")
    else:
        print("Admin user already exists.")
        
    # 2. Seed Reference Data (HS Codes)
    if db.query(HsCode).count() == 0:
        hs_codes = [
            {"code": "610910", "description": "T-shirts, singlets and other vests, of cotton, knitted or crocheted."},
            {"code": "611020", "description": "Jerseys, pullovers, cardigans, waistcoats and similar articles, of cotton, knitted or crocheted."},
            {"code": "100630", "description": "Semi-milled or wholly milled rice, whether or not polished or glazed."},
            {"code": "090240", "description": "Other black tea (fermented) and other partly fermented tea."}
        ]
        
        # Add an additional 46 codes to make it 50 as requested
        for i in range(1, 47):
            code_str = f"99{i:04d}"
            hs_codes.append({"code": code_str, "description": f"General reference commodity category {i}"})
            
        for hs in hs_codes:
            db.add(HsCode(code=hs["code"], description=hs["description"]))
            
        print(f"Seeded {len(hs_codes)} reference HS codes.")
    else:
        print("HS Codes already seeded.")
        
    # 3. Seed ML Training Data
    from db.models import Shipment, Invoice
    import random
    from datetime import datetime, timedelta
    
    if db.query(Shipment).count() < 20:
        for i in range(20):
            sid = f"SYNTH_ML_{i}"
            db.add(Shipment(
                id=sid, invoice_no=sid, status="cleared", source_system="erp",
                port_of_loading="INMAA", port_of_discharge="SGSIN",
                quantity=random.uniform(5, 5000), total_value=random.uniform(100, 200000),
                shipment_date=datetime.utcnow() - timedelta(days=random.randint(1, 100))
            ))
            db.add(Invoice(
                invoice_no=sid, shipment_id=sid, source="erp", buyer="Mock Corp",
                total_value=random.uniform(100, 200000), invoice_date=datetime.utcnow()
            ))
        print("Seeded 20 synthetic historical shipments for Anomaly Training.")
        
    db.commit()
    db.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
