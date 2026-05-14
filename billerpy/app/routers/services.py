from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from .. import database, models

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

@router.get("/")
def list_services(request: Request, db: Session = Depends(database.get_db)):
    services = db.query(models.Service).all()
    company_settings = db.query(models.Settings).first()
    return templates.TemplateResponse(request, "services.html", {
        "request": request, 
        "services": services,
        "title": "Services",
        "company_settings": company_settings
    })

@router.post("/new")
def create_service(
    request: Request,
    name: str = Form(...),
    hsn: str = Form(None),
    db: Session = Depends(database.get_db)
):
    new_service = models.Service(
        name=name,
        hsn=hsn
    )
    db.add(new_service)
    db.commit()
    return RedirectResponse(url="/services", status_code=303)

@router.post("/{id}/edit")
def edit_service(
    id: int,
    name: str = Form(...),
    hsn: str = Form(None),
    db: Session = Depends(database.get_db)
):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        return RedirectResponse(url="/services", status_code=303)
    
    service.name = name
    service.hsn = hsn
    db.commit()
    return RedirectResponse(url="/services", status_code=303)

@router.post("/{id}/delete")
def delete_service(id: int, db: Session = Depends(database.get_db)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if service:
        db.delete(service)
        db.commit()
    return RedirectResponse(url="/services", status_code=303)
