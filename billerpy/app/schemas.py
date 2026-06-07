from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import date, datetime
from enum import Enum

class InvoiceStatus(str, Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PAID = "Paid"
    OVERDUE = "Overdue"

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus

class ClientBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    amount: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: date
    bill_date: Optional[date] = None
    items_json: str = "[]"
    customer_gstin: Optional[str] = None
    notes: Optional[str] = None
    invoice_number: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    client_id: int

class Invoice(InvoiceBase):
    id: int
    created_at: datetime
    client_id: int
    
    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None
    date: date
    receipt_url: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    name: str
    hsn: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
