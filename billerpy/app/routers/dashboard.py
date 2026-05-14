from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import database, models

router = APIRouter()

from ..utils import get_path
templates = Jinja2Templates(directory=get_path("app/templates"))

@router.get("/")
def dashboard(request: Request, db: Session = Depends(database.get_db)):
    # Calculate totals
    paid_invoices = db.query(models.Invoice).filter(models.Invoice.status == models.InvoiceStatus.PAID).all()
    total_revenue = sum(inv.amount or 0 for inv in paid_invoices)
    
    pending_invoices = db.query(models.Invoice).filter(models.Invoice.status != models.InvoiceStatus.PAID).all()
    pending_payments = sum(inv.amount or 0 for inv in pending_invoices)
    
    all_expenses = db.query(models.Expense).all()
    total_expenses = sum(exp.amount or 0 for exp in all_expenses)
    
    net_profit = total_revenue - total_expenses
    
    # Monthly Revenue Trend
    from sqlalchemy import func, extract
    import datetime
    
    current_year = datetime.datetime.now().year
    
    # Initialize 12 months with 0
    monthly_data = {month: 0 for month in range(1, 13)}
    
    revenue_by_month = db.query(
        extract('month', models.Invoice.created_at).label('month'),
        func.sum(models.Invoice.amount).label('total')
    ).filter(
        extract('year', models.Invoice.created_at) == current_year,
        models.Invoice.status == models.InvoiceStatus.PAID
    ).group_by(extract('month', models.Invoice.created_at)).all()
    
    for r in revenue_by_month:
        if r.month is not None:
            monthly_data[int(r.month)] = r.total or 0
        
    # Convert to list for template [Jan, Feb, ... Dec]
    monthly_revenue = list(monthly_data.values())
    
    # Calculate max revenue for chart scaling (avoid division by zero)
    max_revenue = max(monthly_revenue) if monthly_revenue and max(monthly_revenue) > 0 else 1

    recent_invoices = db.query(models.Invoice).order_by(models.Invoice.created_at.desc()).limit(5).all()

    company_settings = db.query(models.Settings).first()

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request, 
        "title": "Dashboard",
        "total_revenue": total_revenue,
        "pending_payments": pending_payments,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "invoices": recent_invoices,
        "monthly_revenue": monthly_revenue,
        "max_revenue": max_revenue,
        "company_settings": company_settings
    })
