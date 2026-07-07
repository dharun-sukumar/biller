from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from .. import database, models
from ..client_import import parse_clients_xlsx

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))


def _clean(value: str | None) -> str | None:
    if value and value.strip():
        return value.strip()
    return None


@router.get("/")
def list_clients(request: Request, db: Session = Depends(database.get_db)):
    clients = db.query(models.Client).all()
    company_settings = db.query(models.Settings).first()
    return templates.TemplateResponse(request, "clients.html", {
        "request": request, 
        "clients": clients,
        "title": "Clients",
        "company_settings": company_settings,
        "upload_result": {
            "created": request.query_params.get("created"),
            "skipped": request.query_params.get("skipped"),
            "error": request.query_params.get("error"),
        },
    })

@router.post("/new")
def create_client(
    name: str = Form(...),
    person_name: str = Form(None),
    tan: str = Form(None),
    pan: str = Form(None),
    gstin: str = Form(None),
    phone: str = Form(None),
    pr_phone: str = Form(None),
    pr_mobile: str = Form(None),
    db: Session = Depends(database.get_db)
):
    new_client = models.Client(
        name=name,
        person_name=_clean(person_name),
        tan=_clean(tan),
        pan=_clean(pan),
        gstin=_clean(gstin),
        phone=_clean(phone),
        pr_phone=_clean(pr_phone),
        pr_mobile=_clean(pr_mobile),
    )
    db.add(new_client)
    db.commit()
    return RedirectResponse(url="/clients", status_code=303)

@router.post("/bulk-upload")
async def bulk_upload_clients(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        query = urlencode({"error": "Please upload a valid .xlsx file."})
        return RedirectResponse(url=f"/clients?{query}", status_code=303)

    file_bytes = await file.read()
    clients_data, parse_errors = parse_clients_xlsx(file_bytes)

    if not clients_data and parse_errors:
        query = urlencode({"error": parse_errors[0]})
        return RedirectResponse(url=f"/clients?{query}", status_code=303)

    created = 0
    skipped = len(parse_errors)

    for client_data in clients_data:
        db.add(models.Client(
            name=client_data["name"],
            tan=client_data.get("tan"),
            pan=client_data.get("pan"),
            person_name=client_data.get("person_name"),
            gstin=client_data.get("gstin"),
            phone=client_data.get("phone"),
            pr_phone=client_data.get("pr_phone"),
            pr_mobile=client_data.get("pr_mobile"),
        ))
        created += 1

    db.commit()

    if not created and not skipped:
        query = urlencode({"error": "No client rows were found in the spreadsheet."})
        return RedirectResponse(url=f"/clients?{query}", status_code=303)

    query = urlencode({"created": created, "skipped": skipped})
    return RedirectResponse(url=f"/clients?{query}", status_code=303)

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
    person_name: str = Form(None),
    tan: str = Form(None),
    pan: str = Form(None),
    gstin: str = Form(None),
    phone: str = Form(None),
    pr_phone: str = Form(None),
    pr_mobile: str = Form(None),
    redirect_to: str = Form(None),
    db: Session = Depends(database.get_db)
):
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        return RedirectResponse(url="/clients", status_code=303)
    
    client.name = name
    client.person_name = _clean(person_name)
    client.tan = _clean(tan)
    client.pan = _clean(pan)
    client.gstin = _clean(gstin)
    client.phone = _clean(phone)
    client.pr_phone = _clean(pr_phone)
    client.pr_mobile = _clean(pr_mobile)
    db.commit()

    if redirect_to and redirect_to.startswith("/clients/"):
        return RedirectResponse(url=redirect_to, status_code=303)
    return RedirectResponse(url="/clients", status_code=303)
