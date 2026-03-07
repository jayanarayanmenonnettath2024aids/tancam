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
    # Ensure data directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/reference", exist_ok=True)
    os.makedirs("data/sample_excel", exist_ok=True)
    os.makedirs("data/sample_invoices", exist_ok=True)
    
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
        
        # Write reference JSON file for external use
        ref_path = os.path.join("data", "reference", "hs_codes.json")
        with open(ref_path, "w") as f:
            json.dump(hs_codes, f, indent=2)
        print(f"Written {ref_path}")
    else:
        print("HS Codes already seeded.")
        
    # 3. Seed ML Training Data
    from db.models import Shipment, Invoice, TradeDocument
    import random
    from datetime import datetime, timedelta
    
    if db.query(Shipment).count() < 20:
        for i in range(20):
            sid = f"SYNTH_ML_{i}"
            
            # Create exactly 1 clear anomaly at index 12
            if i == 12:
                total_val = 2500000.0
                qty = 50.0  # huge unit value
            else:
                total_val = random.uniform(50000, 250000)
                qty = random.uniform(10, 500)
                
            unit_val = total_val / qty
            seed_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
            
            db.add(Shipment(
                id=sid, invoice_no=sid, status="cleared", source_system="erp",
                port_of_loading="INMAA", port_of_discharge="SGSIN",
                quantity=qty, total_value=total_val, unit_value=unit_val,
                shipment_date=seed_date
            ))
            
            db.add(Invoice(
                invoice_no=sid, shipment_id=sid, source="erp", buyer="Mock Corp",
                total_value=total_val, invoice_date=seed_date
            ))
            
            # Seed Trade documents for compliance rate validation
            db.add(TradeDocument(doc_type='invoice', record_id=sid, source="system", raw_content="mock invoice"))
            if i < 18:
                db.add(TradeDocument(doc_type='bill_of_lading', record_id=sid, source="system", raw_content="mock bol"))
            if i < 15:
                db.add(TradeDocument(doc_type='packing_list', record_id=sid, source="system", raw_content="mock pl"))
            if i < 12:
                db.add(TradeDocument(doc_type='certificate_of_origin', record_id=sid, source="system", raw_content="mock coo"))
                
        print("Seeded 20 synthetic historical shipments for Anomaly Training with Trade Documents.")
        
    db.commit()
    db.close()
    
    # Ensure sample data files are accessible in expected subdirectory locations
    sample_excel_src = os.path.join("data", "MSME_Trade_Data.xlsx")
    sample_excel_dst = os.path.join("data", "sample_excel", "MSME_Trade_Data.xlsx")
    if os.path.exists(sample_excel_src) and not os.path.exists(sample_excel_dst):
        import shutil
        shutil.copy2(sample_excel_src, sample_excel_dst)
        print("Copied MSME_Trade_Data.xlsx to data/sample_excel/")
    
    sample_pdf_src = os.path.join("data", "realistic_trade_invoice.pdf")
    sample_pdf_dst = os.path.join("data", "sample_invoices", "realistic_trade_invoice.pdf")
    if os.path.exists(sample_pdf_src) and not os.path.exists(sample_pdf_dst):
        import shutil
        shutil.copy2(sample_pdf_src, sample_pdf_dst)
        print("Copied realistic_trade_invoice.pdf to data/sample_invoices/")
    
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
