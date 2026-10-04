from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    UploadFile
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Invoice, Item, Setting


TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


router = APIRouter(
    tags=["Dashboard"]
)


def get_setting(
    db: Session,
    key: str,
    default: str = ""
):

    setting = (
        db.query(Setting)
        .filter(Setting.key == key)
        .first()
    )

    if setting:
        return setting.value

    return default


@router.get(
    "/dashboard",
    include_in_schema=False
)
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    today = datetime.now().strftime(
        "%d-%b-%Y"
    )

    total_products = (
        db.query(func.count(Item.name))
        .scalar()
        or 0
    )

    total_stock = (
        db.query(
            func.coalesce(
                func.sum(Item.stock),
                0
            )
        )
        .scalar()
        or 0
    )

    total_invoices = (
        db.query(func.count(Invoice.id))
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Invoice.total_amount),
                0
            )
        )
        .scalar()
        or 0
    )

    today_revenue = (
        db.query(
            func.coalesce(
                func.sum(Invoice.total_amount),
                0
            )
        )
        .filter(
            Invoice.date.like(
                f"{today}%"
            )
        )
        .scalar()
        or 0
    )

    today_invoices = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.date.like(
                f"{today}%"
            )
        )
        .scalar()
        or 0
    )

    low_stock = (
        db.query(Item)
        .filter(Item.stock <= 5)
        .order_by(Item.stock.asc())
        .all()
    )

    recent_invoices = (
        db.query(Invoice)
        .order_by(
            Invoice.invoice_id.desc()
        )
        .limit(8)
        .all()
    )

    return templates.TemplateResponse(
    request=request,
    name="dashboard.html",
    context={
        "request": request,
        "store_name": get_setting(
            db,
            "store_name",
            "BillBook Store"
        ),
        "total_products": total_products,
        "total_stock": total_stock,
        "total_invoices": total_invoices,
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "today_invoices": today_invoices,
        "low_stock": low_stock,
        "recent_invoices": recent_invoices,
    }
)

@router.get(
    "/settings",
    include_in_schema=False
)
def settings_page(
    request: Request,
    db: Session = Depends(get_db)
):

    return templates.TemplateResponse(
    request=request,
    name="settings.html",
    context={
        "request": request,
        "store_name": get_setting(
            db,
            "store_name",
            "BillBook Store"
        ),
        "store_phone": get_setting(
            db,
            "store_phone",
            "+91 98765 43210"
        ),
        "store_address": get_setting(
            db,
            "store_address",
            "Main Market, City Center"
        )
    }
)

@router.post(
    "/settings",
    include_in_schema=False
)
async def save_settings(
    request: Request,
    store_name: str = Form(...),
    store_phone: str = Form(""),
    store_address: str = Form(""),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):

    values = {
        "store_name":
            store_name.strip()
            or "BillBook Store",

        "store_phone":
            store_phone.strip(),

        "store_address":
            store_address.strip()
    }

    for key, value in values.items():

        setting = (
            db.query(Setting)
            .filter(Setting.key == key)
            .first()
        )

        if setting:
            setting.value = value

        else:
            db.add(
                Setting(
                    key=key,
                    value=value
                )
            )

    if logo and logo.filename:

        allowed = {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        }

        suffix = Path(
            logo.filename
        ).suffix.lower()

        if suffix in allowed:

            upload_dir = (
                request.app.state.upload_dir
            )

            upload_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            target = (
                upload_dir /
                "store_logo.png"
            )

            data = await logo.read()

            target.write_bytes(data)

    db.commit()

    return RedirectResponse(
    "/settings?saved=1",
    status_code=303
)