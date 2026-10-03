from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy import delete

from ..database import get_db
from ..models import Item, InvoiceItem


TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get(
    "",
    include_in_schema=False
)
def products_page(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db)
):

    query = db.query(Item)

    if q.strip():

        search = f"%{q.strip()}%"

        query = query.filter(
            Item.name.ilike(search)
        )

    items = (
        query
        .order_by(Item.name.asc())
        .all()
    )

    return templates.TemplateResponse(
    request=request,
    name="products.html",
    context={
        "request": request,
        "items": items,
        "q": q
    }
)


@router.post(
    "/save",
    include_in_schema=False
)
def save_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    db: Session = Depends(get_db)
):

    name = name.strip()

    if (
        not name
        or price <= 0
        or stock < 0
    ):
        return RedirectResponse(
            "/products",
            status_code=303
        )

    item = (
        db.query(Item)
        .filter(Item.name == name)
        .first()
    )

    if item:

        item.price = price
        item.stock = stock

    else:

        db.add(
            Item(
                name=name,
                price=price,
                stock=stock
            )
        )

    db.commit()

    return RedirectResponse(
        "/products",
        status_code=303
    )


@router.post(
    "/delete/{name}",
    include_in_schema=False
)
def delete_product(
    name: str,
    db: Session = Depends(get_db)
):
    item = (
        db.query(Item)
        .filter(Item.name == name)
        .first()
    )

    if not item:
        return RedirectResponse(
            "/products",
            status_code=303
        )

    # Delete the product directly from the items table.
    #
    # We intentionally do NOT delete InvoiceItem records.
    # InvoiceItem contains a historical snapshot of the
    # product name, price, quantity, and amount.
    db.execute(
        delete(Item).where(
            Item.name == name
        )
    )

    db.commit()

    return RedirectResponse(
        "/products",
        status_code=303
    )

@router.get("/api")
def products_api(
    db: Session = Depends(get_db)
):

    items = (
        db.query(Item)
        .order_by(Item.name.asc())
        .all()
    )

    return [
        {
            "name": item.name,
            "price": item.price,
            "stock": item.stock
        }
        for item in items
    ]