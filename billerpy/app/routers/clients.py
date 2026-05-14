from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from .. import database, models

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

@router.get("/")
def list_clients(request: Request, db: Session = Depends(database.get_db)):
    clients = db.query(models.Client).all()
    company_settings = db.query(models.Settings).first()
    return templates.TemplateResponse(request, "clients.html", {
        "request": request, 
        "clients": clients,
        "title": "Clients",
        "company_settings": company_settings
    })

@router.post("/new")
def create_client(
    request: Request,
    name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    address: str = Form(None),
    gstin: str = Form(None),
    db: Session = Depends(database.get_db)
):
    new_client = models.Client(
        name=name,
        email=email if email and email.strip() else None,
        phone=phone,
        address=address,
        gstin=gstin if gstin and gstin.strip() else None
    )
    db.add(new_client)
    db.commit()
    return RedirectResponse(url="/clients", status_code=303)

@router.get("/{id}")
def view_client(id: int, request: Request, db: Session = Depends(database.get_db)):
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        return RedirectResponse(url="/clients", status_code=303)
    
    company_settings = db.query(models.Settings).first()
    
    return templates.TemplateResponse(request, "client_view.html", {
        "request": request,
        "client": client,
        "invoices": client.invoices,
        "title": f"Client - {client.name}",
        "company_settings": company_settings
    })

@router.post("/{id}/edit")
def edit_client(
    id: int,
    name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    address: str = Form(None),
    gstin: str = Form(None),
    db: Session = Depends(database.get_db)
):
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        return RedirectResponse(url="/clients", status_code=303)
    
    client.name = name
    client.email = email if email and email.strip() else None
    client.phone = phone
    client.address = address
    client.gstin = gstin if gstin and gstin.strip() else None
    db.commit()
    return RedirectResponse(url="/clients", status_code=303)
