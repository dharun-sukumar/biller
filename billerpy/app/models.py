from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Enum
from sqlalchemy.orm import relationship
from .database import Base
import datetime
import enum

class InvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PAID = "Paid"
    OVERDUE = "Overdue"

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String)
    address = Column(String)
    gstin = Column(String, nullable=True)
    tan = Column(String, nullable=True)
    pan = Column(String, nullable=True)
    person_name = Column(String, nullable=True)
    pr_phone = Column(String, nullable=True)
    pr_mobile = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoices = relationship("Invoice", back_populates="client")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, nullable=True)  # Custom invoice number
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Float)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    customer_gstin = Column(String)
    
    # Store items as a JSON string for simplicity in this version, 
    # or could be a relationship to an InvoiceItem table. 
    # For now, let's keep it simple.
    items_json = Column(String, default="[]") 

    # Snapshot of Company Details at time of creation
    from_company_name = Column(String)
    from_address_line1 = Column(String)
    from_address_line2 = Column(String)
    from_phone = Column(String)
    from_email = Column(String)
    from_pan_no = Column(String)
    from_gst_no = Column(String)
    
    # Snapshot of Payment Details
    bank_name = Column(String)
    branch_name = Column(String)  # Added branch_name
    account_no = Column(String)
    ifsc_code = Column(String)
    
    # Snapshot of Branding
    logo_path = Column(String)
    qr_code_path = Column(String)
    signature_path = Column(String)
    
    # Notes
    notes = Column(String, nullable=True)

    client = relationship("Client", back_populates="invoices")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    amount = Column(Float)
    category = Column(String)
    date = Column(Date, default=datetime.datetime.utcnow)
    receipt_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    hsn = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, default="SRI ASSOCIATES")
    address_line1 = Column(String, default="12/7 A Arangasamy nagar, Civil Aerodome Post")
    address_line2 = Column(String, default="Airport road, Sitra, Coimbatore - 641 014")
    phone = Column(String, default="+91 77088 10444, +91 94885 84097")
    email = Column(String, default="sriassociates5611@gmail.com")
    pan_no = Column(String)
    gst_no = Column(String)
    
    # Banking Details
    bank_name = Column(String, default="Punjab National Bank")
    branch_name = Column(String, default="AVINASHI ROAD BRANCH")
    account_no = Column(String, default="10441132000217")
    ifsc_code = Column(String, default="PUNB0104410")
    
    logo_path = Column(String, default="/static/logo.png")
    qr_code_path = Column(String)
    signature_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
