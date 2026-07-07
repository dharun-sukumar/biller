from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import dashboard, clients, invoices, expenses, profile, services
# Note: clients, invoices, expenses routers will be created later, commenting out for now if they cause error, 
# but for avoiding import errors I will just import dashboard for now.

# Create tables
Base.metadata.create_all(bind=engine)

# Auto-migration for new columns
def run_migrations():
    import sqlite3
    try:
        from .utils import get_data_path
        conn = sqlite3.connect(get_data_path('billerpy.db'))
        cursor = conn.cursor()
        
        # Check settings
        cursor.execute("PRAGMA table_info(settings)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols and "branch_name" not in cols:
            cursor.execute("ALTER TABLE settings ADD COLUMN branch_name VARCHAR")
        if cols and "signature_path" not in cols:
            cursor.execute("ALTER TABLE settings ADD COLUMN signature_path VARCHAR")
        if cols and "pan_no" not in cols:
            cursor.execute("ALTER TABLE settings ADD COLUMN pan_no VARCHAR")
        if cols and "gst_no" not in cols:
            cursor.execute("ALTER TABLE settings ADD COLUMN gst_no VARCHAR")

        # Create services table manually if not there
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                hsn VARCHAR,
                created_at DATETIME
            )
        ''')
            
        # Check invoices
        cursor.execute("PRAGMA table_info(invoices)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols and "invoice_number" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_number VARCHAR")
        if cols and "branch_name" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN branch_name VARCHAR")
        if cols and "signature_path" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN signature_path VARCHAR")
        if cols and "from_pan_no" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN from_pan_no VARCHAR")
        if cols and "from_gst_no" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN from_gst_no VARCHAR")
        if cols and "customer_gstin" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN customer_gstin VARCHAR")
        if cols and "notes" not in cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN notes VARCHAR")
            
        # Check clients for new columns
        cursor.execute("PRAGMA table_info(clients)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            client_migrations = {
                "gstin": "ALTER TABLE clients ADD COLUMN gstin VARCHAR",
                "tan": "ALTER TABLE clients ADD COLUMN tan VARCHAR",
                "pan": "ALTER TABLE clients ADD COLUMN pan VARCHAR",
                "person_name": "ALTER TABLE clients ADD COLUMN person_name VARCHAR",
                "pr_phone": "ALTER TABLE clients ADD COLUMN pr_phone VARCHAR",
                "pr_mobile": "ALTER TABLE clients ADD COLUMN pr_mobile VARCHAR",
            }
            for col, sql in client_migrations.items():
                if col not in cols:
                    cursor.execute(sql)
            
        conn.commit()
        conn.close()
    except:
        pass

run_migrations()

app = FastAPI(title="BillerPy")

from .utils import get_path, get_persistent_path

app.mount("/static", StaticFiles(directory=get_path("app/static")), name="static")
app.mount("/uploads", StaticFiles(directory=get_persistent_path("uploads")), name="uploads")

app.include_router(dashboard.router)
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(services.router, prefix="/services", tags=["services"])

@app.get("/")
def root():
    return {"message": "Welcome to BillerPy"}
