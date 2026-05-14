from fastapi import APIRouter, Request, Depends, Body
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import APIRouter, Request, Depends, Body, HTTPException
from .. import database, models, schemas
import json

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

def get_next_invoice_number(db: Session) -> str:
    """Generate the next invoice number in sequence (INV-001, INV-002, etc.)"""
    latest = db.query(models.Invoice).filter(
        models.Invoice.invoice_number.isnot(None)
    ).order_by(models.Invoice.id.desc()).first()
    
    if not latest or not latest.invoice_number:
        return "INV-001"
    
    # Extract numeric part from invoice_number
    try:
        parts = latest.invoice_number.split('-')
        if len(parts) > 1:
            num = int(parts[-1])
            return f"INV-{str(num + 1).zfill(3)}"
    except (ValueError, IndexError):
        pass
    
    # Fallback: use invoice ID count
    count = db.query(models.Invoice).count()
    return f"INV-{str(count + 1).zfill(3)}"

def is_invoice_number_unique(db: Session, invoice_number: str, exclude_id: int = None) -> bool:
    """Check if invoice_number is unique (allowing nulls for multiple invoices without number)"""
    query = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice_number
    )
    if exclude_id:
        query = query.filter(models.Invoice.id != exclude_id)
    return query.first() is None

@router.get("/")
def list_invoices(request: Request, db: Session = Depends(database.get_db)):
    invoices = db.query(models.Invoice).order_by(models.Invoice.id.desc()).all()
    clients = db.query(models.Client).all()
    company_settings = db.query(models.Settings).first()
    return templates.TemplateResponse(request, "invoices.html", {
        "request": request, 
        "invoices": invoices,
        "clients": clients,
        "title": "Invoices",
        "company_settings": company_settings
    })

@router.get("/new")
def new_invoice_form(request: Request, db: Session = Depends(database.get_db)):
    import datetime
    today_date = datetime.date.today().isoformat()
    clients = db.query(models.Client).all()
    services = db.query(models.Service).all()
    company_settings = db.query(models.Settings).first()
    next_invoice_number = get_next_invoice_number(db)
    return templates.TemplateResponse(request, "invoice_editor.html", {
        "request": request,
        "clients": clients,
        "today_date": today_date,
        "services": services,
        "title": "New Invoice",
        "company_settings": company_settings,
        "default_invoice_number": next_invoice_number
    })

@router.post("/new")
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(database.get_db)):
    # Validate invoice number is unique if provided
    if invoice.invoice_number and invoice.invoice_number.strip():
        if not is_invoice_number_unique(db, invoice.invoice_number):
            return JSONResponse(
                status_code=400,
                content={"message": f"Invoice number '{invoice.invoice_number}' already exists. Please use a unique number."}
            )
    
    # Fetch current settings to snapshot them
    settings = db.query(models.Settings).first()
    if not settings:
        # Create default settings if not exists to avoid errors
        settings = models.Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Fetch client to get GSTIN
    client = db.query(models.Client).filter(models.Client.id == invoice.client_id).first()
    customer_gstin = client.gstin if client else None

    new_invoice = models.Invoice(
        client_id=invoice.client_id,
        amount=invoice.amount,
        status=invoice.status,
        due_date=invoice.due_date,
        items_json=invoice.items_json,
        customer_gstin=customer_gstin,
        notes=invoice.notes,
        invoice_number=invoice.invoice_number,
        
        # Snapshots
        from_company_name=settings.company_name,
        from_address_line1=settings.address_line1,
        from_address_line2=settings.address_line2,
        from_phone=settings.phone,
        from_email=settings.email,
        from_pan_no=settings.pan_no,
        from_gst_no=settings.gst_no,
        bank_name=settings.bank_name,
        branch_name=settings.branch_name,
        account_no=settings.account_no,
        ifsc_code=settings.ifsc_code,
        logo_path=settings.logo_path,
        qr_code_path=settings.qr_code_path,
        signature_path=settings.signature_path
    )
    db.add(new_invoice)
    db.commit()
    return JSONResponse(content={"message": "Invoice created successfully", "id": new_invoice.id})

@router.get("/{id}")
def view_invoice(id: int, request: Request, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload
    try:
        # Fetch invoice with client details
        invoice = db.query(models.Invoice).options(joinedload(models.Invoice.client)).filter(models.Invoice.id == id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        settings = db.query(models.Settings).first() or models.Settings()
        
        # Parse items JSON safely
        try:
            items = json.loads(invoice.items_json) if invoice.items_json else []
            for item in items:
                price = item.get('price')
                item['price'] = float(price) if price is not None else 0.0
        except:
            items = []
        
        # Date formatting
        date_str = invoice.created_at.strftime('%d/%m/%Y') if invoice.created_at else "N/A"
        
        return templates.TemplateResponse(request, "invoice_view_safe.html", {
            "request": request,
            "invoice": invoice,
            "items": items,
            "settings": settings,
            "date_str": date_str,
            "title": f"Invoice #{invoice.id}",
            "company_settings": settings
        })
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"ERROR: {err}")
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@router.put("/{id}/status")
def update_invoice_status(id: int, status_update: schemas.InvoiceStatusUpdate, db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    
    invoice.status = status_update.status
    db.commit()
    return {"message": "Status updated successfully", "new_status": invoice.status}

@router.put("/{id}/invoice-number")
def update_invoice_number(id: int, invoice_number: dict = Body(...), db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    
    if invoice.status != models.InvoiceStatus.DRAFT:
        return JSONResponse(status_code=400, content={"message": "Only draft invoices can have their number changed"})
    
    new_number = invoice_number.get("invoice_number")
    if new_number and new_number.strip():
        if new_number != invoice.invoice_number:
            if not is_invoice_number_unique(db, new_number, exclude_id=id):
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Invoice number '{new_number}' already exists. Please use a unique number."}
                )
    
    invoice.invoice_number = new_number
    db.commit()
    return {"message": "Invoice number updated successfully", "invoice_number": invoice.invoice_number}

@router.put("/{id}/details")
def update_invoice_details(
    id: int, 
    client_id: int = Body(...),
    amount: float = Body(...),
    due_date: str = Body(...),
    db: Session = Depends(database.get_db)
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    
    if invoice.status != models.InvoiceStatus.DRAFT:
        return JSONResponse(status_code=400, content={"message": "Only draft invoices can be edited"})

    import datetime
    invoice.client_id = client_id
    invoice.amount = amount
    # Convert string date (YYYY-MM-DD) to python date object
    if isinstance(due_date, str):
        invoice.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
    else:
        invoice.due_date = due_date
    
    # Update snapshots if client changed? 
    # Usually snapshots are taken at creation, but if we change client, we might want to keep old snapshots 
    # OR update them. Use Case: "Draft" implies it's not final. 
    # But user didn't ask to update snapshots. I'll stick to updating the foreign key.
    
    db.commit()
    db.commit()
    return {"message": "Invoice details updated successfully"}

@router.get("/{id}/edit")
def edit_invoice_form(id: int, request: Request, db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != models.InvoiceStatus.DRAFT:
        # Ideally should redirect or show error, but for now redirecting to view
        # return RedirectResponse(url=f"/invoices/{id}")
        pass

    clients = db.query(models.Client).all()
    services = db.query(models.Service).all()
    company_settings = db.query(models.Settings).first()
    
    # Parse items
    try:
        items = json.loads(invoice.items_json) if invoice.items_json else []
    except:
        items = []

    import datetime
    return templates.TemplateResponse(request, "invoice_editor.html", {
        "request": request,
        "invoice": invoice,
        "clients": clients,
        "start_date": invoice.created_at.date().isoformat() if invoice.created_at else datetime.date.today().isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date and hasattr(invoice.due_date, 'isoformat') else (invoice.due_date if invoice.due_date else ""),
        "items": items,
        "services": services,
        "title": f"Edit Invoice #{invoice.id}",
        "company_settings": company_settings,
        "is_edit": True
    })

@router.put("/{id}")
def edit_invoice_submit(id: int, invoice_update: schemas.InvoiceCreate, db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        return JSONResponse(status_code=404, content={"message": "Invoice not found"})

    if invoice.status != models.InvoiceStatus.DRAFT:
        return JSONResponse(status_code=400, content={"message": "Only draft invoices can be edited"})

    # Validate invoice number is unique if provided and different from current
    if invoice_update.invoice_number and invoice_update.invoice_number.strip():
        if invoice_update.invoice_number != invoice.invoice_number:
            if not is_invoice_number_unique(db, invoice_update.invoice_number, exclude_id=id):
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Invoice number '{invoice_update.invoice_number}' already exists. Please use a unique number."}
                )

    invoice.client_id = invoice_update.client_id
    invoice.amount = invoice_update.amount
    invoice.due_date = invoice_update.due_date
    invoice.items_json = invoice_update.items_json
    invoice.customer_gstin = invoice_update.customer_gstin
    invoice.notes = invoice_update.notes
    invoice.invoice_number = invoice_update.invoice_number
    # Status usually remains Draft or whatever was passed, but usually we don't update status here 
    # unless user explicitly changes it. For now, we trust the form doesn't change status implicity 
    # OR we keep it as is. The schema has 'status', let's use it if user wants to change it via this form.
    invoice.status = invoice_update.status 

    db.commit()
    return JSONResponse(content={"message": "Invoice updated successfully", "id": invoice.id})

@router.delete("/{id}")
def delete_invoice(id: int, db: Session = Depends(database.get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    
    if invoice.status != models.InvoiceStatus.DRAFT:
        return JSONResponse(status_code=400, content={"message": "Only draft invoices can be deleted"})
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}
