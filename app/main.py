from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import Base, SessionLocal, engine
from .models import Item, Setting
from .routers import dashboard, invoices, products


BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR = STATIC_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Create database tables
Base.metadata.create_all(bind=engine)


# Default data
with SessionLocal() as db:

    if db.query(Item).count() == 0:

        db.add_all([
            Item(
                name="Apple",
                price=20.0,
                stock=100
            ),
            Item(
                name="Banana",
                price=10.0,
                stock=150
            ),
            Item(
                name="Milk",
                price=50.0,
                stock=40
            ),
            Item(
                name="Bread",
                price=40.0,
                stock=30
            ),
        ])

    default_settings = {
        "store_name": "QuickBill Store",
        "store_phone": "+91 98765 43210",
        "store_address": "Main Market, City Center",
    }

    for key, value in default_settings.items():

        existing = (
            db.query(Setting)
            .filter(Setting.key == key)
            .first()
        )

        if existing is None:
            db.add(
                Setting(
                    key=key,
                    value=value
                )
            )

    db.commit()


app = FastAPI(
    title="QuickBill",
    description="Billing and Inventory Management System",
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


app.state.upload_dir = UPLOAD_DIR


@app.get("/", include_in_schema=False)
def root():

    from fastapi.responses import RedirectResponse

    return RedirectResponse(
        url="/dashboard"
    )


@app.get(
    "/health",
    include_in_schema=False
)
def health():

    return {
        "status": "ok"
    }


app.include_router(
    dashboard.router
)

app.include_router(
    products.router
)

app.include_router(
    invoices.router
)