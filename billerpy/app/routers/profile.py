from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models, database
import shutil
import os
import uuid

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

@router.get("/", response_class=HTMLResponse)
def read_profile(request: Request, db: Session = Depends(database.get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        # Create default settings if not exists
        settings = models.Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return templates.TemplateResponse(request, "profile.html", {
        "request": request, 
        "settings": settings, 
        "title": "Company Profile",
        "os_path_exists": os.path.exists,
        "company_settings": settings
    })

@router.post("/")
def update_profile(
    request: Request,
    company_name: str = Form(...),
    address_line1: str = Form(...),
    address_line2: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    bank_name: str = Form(None),
    branch_name: str = Form(None),
    account_no: str = Form(None),
    ifsc_code: str = Form(None),
    pan_no: str = Form(None),
    gst_no: str = Form(None),
    logo: UploadFile = File(None),
    qr_code: UploadFile = File(None),
    signature: UploadFile = File(None),
    db: Session = Depends(database.get_db)
):
    settings = db.query(models.Settings).first()
    if not settings:
        settings = models.Settings()
        db.add(settings)
    
    settings.company_name = company_name
    settings.address_line1 = address_line1
    settings.address_line2 = address_line2
    settings.phone = phone
    settings.email = email
    settings.bank_name = bank_name
    settings.branch_name = branch_name
    settings.account_no = account_no
    settings.ifsc_code = ifsc_code
    settings.pan_no = pan_no
    settings.gst_no = gst_no

    # Handle Logo Upload
    if logo and logo.filename:
        from ..utils import get_persistent_path
        upload_dir = get_persistent_path("uploads")
        ext = os.path.splitext(logo.filename)[1]
        logo_filename = f"logo_{uuid.uuid4().hex}{ext}"
        logo_path = os.path.join(upload_dir, logo_filename)
        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
        settings.logo_path = f"/uploads/{logo_filename}"

    # Handle QR Code Upload
    if qr_code and qr_code.filename:
        from ..utils import get_persistent_path
        upload_dir = get_persistent_path("uploads")
        ext = os.path.splitext(qr_code.filename)[1]
        qr_filename = f"qr_{uuid.uuid4().hex}{ext}"
        qr_path = os.path.join(upload_dir, qr_filename)
        with open(qr_path, "wb") as buffer:
            shutil.copyfileobj(qr_code.file, buffer)
        settings.qr_code_path = f"/uploads/{qr_filename}"

    # Handle Signature Upload
    if signature and signature.filename:
        from ..utils import get_persistent_path
        upload_dir = get_persistent_path("uploads")
        ext = os.path.splitext(signature.filename)[1]
        sig_filename = f"sig_{uuid.uuid4().hex}{ext}"
        sig_path = os.path.join(upload_dir, sig_filename)
        with open(sig_path, "wb") as buffer:
            shutil.copyfileobj(signature.file, buffer)
        settings.signature_path = f"/uploads/{sig_filename}"

    db.commit()
    
    return RedirectResponse(url="/profile", status_code=303)
