from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Enum, ARRAY, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum('admin', 'analyst', 'viewer', name='user_roles'), nullable=False, default='viewer')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TradeDocument(Base):
    __tablename__ = "trade_documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(Enum('invoice', 'bol', 'packing_list', 'email', 'excel_row', name='doc_types'), nullable=False)
    source = Column(Enum('erp', 'email', 'excel', 'pdf', 'portal', name='source_systems'), nullable=False)
    raw_content = Column(Text)
    # Using JSON decorator/type handles JSON in SQLite too
    extracted_json = Column(JSON, nullable=True)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime)
    status = Column(String, default='pending')
    
class Customer(Base):
    __tablename__ = "customers"
    master_id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True, nullable=False)
    aliases = Column(JSON, nullable=True)
    country = Column(String)
    gstin = Column(String)
    pan = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class Product(Base):
    __tablename__ = "products"
    master_id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True, nullable=False)
    hs_code = Column(String, index=True)
    unit = Column(String)
    aliases = Column(JSON, nullable=True)
    category = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class HsCode(Base):
    __tablename__ = "hs_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(String, primary_key=True, index=True) # Typically invoice_no or specific shipment ID
    invoice_no = Column(String, index=True)
    customer_id = Column(Integer, ForeignKey("customers.master_id"))
    product_id = Column(Integer, ForeignKey("products.master_id"))
    quantity = Column(Float)
    unit_value = Column(Float)
    total_value = Column(Float)
    currency = Column(String, default='INR')
    shipment_date = Column(DateTime)
    status = Column(Enum('pending', 'cleared', 'held', 'rejected', name='shipment_statuses'), default='pending')
    source_system = Column(String)
    port_of_loading = Column(String)
    port_of_discharge = Column(String)
    shipping_bill_no = Column(String)
    clearance_status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String, unique=True, index=True, nullable=False)
    shipment_id = Column(String, ForeignKey("shipments.id"))
    invoice_date = Column(DateTime)
    buyer = Column(String)
    seller = Column(String)
    total_value = Column(Float)
    gst_amount = Column(Float)
    gst_rate = Column(Float)
    customs_duty = Column(Float)
    currency = Column(String, default='INR')
    document_path = Column(String)
    source = Column(String)
    extracted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, ForeignKey("shipments.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    gstin_valid = Column(Boolean)
    gstin_flag = Column(Text)
    hs_code_valid = Column(Boolean)
    hs_code_flag = Column(Text)
    gst_amount_valid = Column(Boolean)
    gst_amount_flag = Column(Text)
    missing_docs = Column(JSON, nullable=True)
    overall_status = Column(Enum('ok', 'warning', 'critical', name='compliance_statuses'))
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String) # 'shipment' or 'invoice'
    record_id = Column(String) # For shipment_id
    anomaly_score = Column(Float)
    is_anomaly = Column(Boolean, default=False)
    description = Column(Text)
    feature_values = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TriggerLog(Base):
    __tablename__ = "trigger_log"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    triggered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    records_affected = Column(Integer, default=0)
    status = Column(String)
    error_message = Column(Text)
    duration_ms = Column(Integer, default=0)
