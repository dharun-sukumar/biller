from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from .. import database, models
import datetime

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

@router.get("/")
def list_expenses(request: Request, db: Session = Depends(database.get_db)):
    expenses = db.query(models.Expense).order_by(models.Expense.date.desc()).all()
    company_settings = db.query(models.Settings).first()
    return templates.TemplateResponse(request, "expenses.html", {
        "request": request, 
        "expenses": expenses,
        "title": "Expenses",
        "company_settings": company_settings
    })

@router.post("/new")
def create_expense(
    request: Request,
    category: str = Form(...),
    amount: float = Form(...),
    description: str = Form(None),
    date: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # date string from form is usually YYYY-MM-DD
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    
    new_expense = models.Expense(
        category=category,
        amount=amount,
        description=description,
        date=date_obj
    )
    db.add(new_expense)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=303)

@router.delete("/{id}")
def delete_expense(id: int, db: Session = Depends(database.get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == id).first()
    if not expense:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"message": "Expense not found"})
    
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
