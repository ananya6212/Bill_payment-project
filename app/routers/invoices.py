from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..database import get_db
from ..models import Item, Invoice, InvoiceItem, Setting


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

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


def get_next_invoice_number(
    db: Session
) -> int:

    last_invoice = (
        db.query(Invoice)
        .order_by(
            Invoice.invoice_id.desc()
        )
        .first()
    )

    if last_invoice is None:
        return 1

    return last_invoice.invoice_id + 1


def calculate_invoice(
    cart_items,
    discount_percent,
    tax_percent
):

    subtotal = sum(
        item["amount"]
        for item in cart_items
    )

    discount_amount = round(
        subtotal * discount_percent / 100,
        2
    )

    taxable_amount = max(
        0,
        subtotal - discount_amount
    )

    tax_amount = round(
        taxable_amount * tax_percent / 100,
        2
    )

    total_amount = round(
        taxable_amount + tax_amount,
        2
    )

    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": discount_amount,
        "taxable_amount": round(
            taxable_amount,
            2
        ),
        "tax_amount": tax_amount,
        "total_amount": total_amount,
    }


# ---------------------------------------------------------
# Invoice History
# ---------------------------------------------------------

@router.get(
    "",
    response_class=HTMLResponse,
    include_in_schema=False
)
def invoices_page(
    request: Request,
    db: Session = Depends(get_db)
):

    invoices = (
        db.query(Invoice)
        .order_by(
            Invoice.invoice_id.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
    request=request,
    name="invoices.html",
    context={
        "request": request,
        "invoices": invoices,
    }
)


# ---------------------------------------------------------
# Create Invoice Page
# ---------------------------------------------------------

@router.get(
    "/new",
    response_class=HTMLResponse,
    include_in_schema=False
)
def new_invoice_page(
    request: Request,
    db: Session = Depends(get_db)
):

    products = (
        db.query(Item)
        .order_by(Item.name.asc())
        .all()
    )

    invoice_number = get_next_invoice_number(
        db
    )

    return templates.TemplateResponse(
    request=request,
    name="create_invoice.html",
    context={
        "request": request,
        "products": products,
        "invoice_number": invoice_number,
        "store_name": get_setting(
            db,
            "store_name",
            "BillBook Store"
        ),
    }
)


# ---------------------------------------------------------
# Create Invoice
# ---------------------------------------------------------

@router.post(
    "/create",
    include_in_schema=False
)
def create_invoice(
    customer_name: str = Form(...),
    product_names: str = Form(""),
    quantities: str = Form(""),
    discount_percent: float = Form(0),
    tax_percent: float = Form(0),
    payment_mode: str = Form("Cash"),
    db: Session = Depends(get_db)
):

    customer_name = customer_name.strip()

    if not customer_name:
        return RedirectResponse(
            "/invoices/new",
            status_code=303
        )

    # -----------------------------------------------------
    # Convert comma-separated form data into lists
    # -----------------------------------------------------

    names = [
        name.strip()
        for name in product_names.split(",")
        if name.strip()
    ]

    qty_values = []

    for value in quantities.split(","):

        value = value.strip()

        if not value:
            continue

        try:
            qty_values.append(
                int(value)
            )
        except ValueError:
            qty_values.append(0)

    # -----------------------------------------------------
    # Validate cart
    # -----------------------------------------------------

    if not names:
        return RedirectResponse(
            "/invoices/new",
            status_code=303
        )

    if len(names) != len(qty_values):
        return RedirectResponse(
            "/invoices/new",
            status_code=303
        )

    cart_items = []

    for name, quantity in zip(
        names,
        qty_values
    ):

        if quantity <= 0:
            continue

        product = (
            db.query(Item)
            .filter(Item.name == name)
            .first()
        )

        if product is None:
            continue

        # Prevent selling more than available stock
        if quantity > product.stock:

            return RedirectResponse(
                "/invoices/new",
                status_code=303
            )

        amount = round(
            product.price * quantity,
            2
        )

        cart_items.append(
            {
                "item": product.name,
                "price": product.price,
                "qty": quantity,
                "amount": amount,
            }
        )

    if not cart_items:

        return RedirectResponse(
            "/invoices/new",
            status_code=303
        )

    # -----------------------------------------------------
    # Sanitize percentages
    # -----------------------------------------------------

    discount_percent = max(
        0,
        min(
            discount_percent,
            100
        )
    )

    tax_percent = max(
        0,
        min(
            tax_percent,
            100
        )
    )

    # -----------------------------------------------------
    # Calculate totals
    # -----------------------------------------------------

    totals = calculate_invoice(
        cart_items,
        discount_percent,
        tax_percent
    )

    # -----------------------------------------------------
    # Generate invoice number
    # -----------------------------------------------------

    invoice_number = get_next_invoice_number(
        db
    )

    date_string = datetime.now().strftime(
        "%d-%b-%Y %H:%M:%S"
    )

    # -----------------------------------------------------
    # Create invoice header
    # -----------------------------------------------------

    invoice = Invoice(
        invoice_id=invoice_number,
        customer_name=customer_name,
        date=date_string,
        subtotal=totals["subtotal"],
        discount=totals["discount_amount"],
        tax=totals["tax_amount"],
        total_amount=totals["total_amount"],
        payment_mode=payment_mode,
    )

    db.add(invoice)

    # Flush so invoice relationship can be used
    db.flush()

    # -----------------------------------------------------
    # Add invoice items + reduce stock
    # -----------------------------------------------------

    for cart_item in cart_items:

        product = (
            db.query(Item)
            .filter(
                Item.name == cart_item["item"]
            )
            .first()
        )

        if product is None:
            continue

        invoice_item = InvoiceItem(
            invoice_id=invoice_number,
            item_name=cart_item["item"],
            quantity=cart_item["qty"],
            price=cart_item["price"],
            amount=cart_item["amount"],
        )

        db.add(invoice_item)

        # Deduct stock
        product.stock -= cart_item["qty"]

    db.commit()

    return RedirectResponse(
        f"/invoices/{invoice_number}",
        status_code=303
    )


# ---------------------------------------------------------
# Invoice Details
# ---------------------------------------------------------

@router.get(
    "/{invoice_id}",
    response_class=HTMLResponse,
    include_in_schema=False
)
def invoice_detail(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_id == invoice_id
        )
        .first()
    )

    if invoice is None:

        return HTMLResponse(
            "Invoice not found",
            status_code=404
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice_id
        )
        .all()
    )

    return templates.TemplateResponse(
    request=request,
    name="invoice.html",
    context={
        "request": request,
        "invoice": invoice,
        "items": items,
        "store_name": get_setting(
            db,
            "store_name",
            "BillBook Store"
        ),
        "store_phone": get_setting(
            db,
            "store_phone",
            ""
        ),
        "store_address": get_setting(
            db,
            "store_address",
            ""
        ),
    }
)
# ---------------------------------------------------------
# Print Invoice
# ---------------------------------------------------------

@router.get(
    "/{invoice_id}/print",
    response_class=HTMLResponse,
    include_in_schema=False
)
def print_invoice(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_id == invoice_id
        )
        .first()
    )

    if invoice is None:
        return HTMLResponse(
            "Invoice not found",
            status_code=404
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice_id
        )
        .all()
    )

    return templates.TemplateResponse(
    request=request,
    name="invoice.html",
    context={
        "request": request,
        "invoice": invoice,
        "items": items,
        "store_name": get_setting(
            db,
            "store_name",
            "BillBook Store"
        ),
        "store_phone": get_setting(
            db,
            "store_phone",
            ""
        ),
        "store_address": get_setting(
            db,
            "store_address",
            ""
        ),
        "auto_print": True,
    }
)

# ---------------------------------------------------------
# PDF Invoice
# ---------------------------------------------------------

@router.get(
    "/{invoice_id}/pdf",
    include_in_schema=False
)
def invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db)
):

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_id == invoice_id
        )
        .first()
    )

    if invoice is None:

        return HTMLResponse(
            "Invoice not found",
            status_code=404
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice_id
        )
        .all()
    )

    store_name = get_setting(
        db,
        "store_name",
        "BillBook Store"
    )

    store_phone = get_setting(
        db,
        "store_phone",
        ""
    )

    store_address = get_setting(
        db,
        "store_address",
        ""
    )

    filename = (
        f"invoice_{invoice.invoice_id}.pdf"
    )

    def generate_pdf():

        import io

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            spaceAfter=10,
        )

        right_style = ParagraphStyle(
            "Right",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        )

        story = []

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        story.append(
            Paragraph(
                store_name,
                title_style
            )
        )

        if store_address:
            story.append(
                Paragraph(
                    store_address,
                    styles["Normal"]
                )
            )

        if store_phone:
            story.append(
                Paragraph(
                    f"Phone: {store_phone}",
                    styles["Normal"]
                )
            )

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                f"<b>Invoice #{invoice.invoice_id}</b>",
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                f"Customer: {invoice.customer_name}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Date: {invoice.date}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Payment Mode: {invoice.payment_mode}",
                styles["Normal"]
            )
        )

        story.append(
            Spacer(1, 20)
        )

        # -------------------------------------------------
        # Items table
        # -------------------------------------------------

        table_data = [
            [
                "#",
                "Item",
                "Price",
                "Qty",
                "Amount"
            ]
        ]

        for index, item in enumerate(
            items,
            start=1
        ):

            table_data.append(
                [
                    str(index),
                    item.item_name,
                    f"₹{item.price:.2f}",
                    str(item.quantity),
                    f"₹{item.amount:.2f}",
                ]
            )

        table = Table(
            table_data,
            colWidths=[
                30,
                220,
                80,
                50,
                90
            ]
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1f2937")
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER"
                    ),
                    (
                        "ALIGN",
                        (2, 1),
                        (-1, -1),
                        "RIGHT"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(1, 20)
        )

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        summary = [
            [
                "Subtotal",
                f"₹{invoice.subtotal:.2f}"
            ],
            [
                "Discount",
                f"- ₹{invoice.discount:.2f}"
            ],
            [
                "GST / Tax",
                f"+ ₹{invoice.tax:.2f}"
            ],
            [
                "Grand Total",
                f"₹{invoice.total_amount:.2f}"
            ],
        ]

        summary_table = Table(
            summary,
            colWidths=[
                350,
                120
            ]
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "ALIGN",
                        (1, 0),
                        (1, -1),
                        "RIGHT"
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold"
                    ),
                    (
                        "LINEABOVE",
                        (0, -1),
                        (-1, -1),
                        1,
                        colors.black
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )

        story.append(
            summary_table
        )

        story.append(
            Spacer(1, 30)
        )

        story.append(
            Paragraph(
                f"Thank you for shopping with {store_name}!",
                styles["Normal"]
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer

    pdf_buffer = generate_pdf()

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )
    
@router.post(
    "/{invoice_id}/delete",
    include_in_schema=False
)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice = (
        db.query(Invoice)
        .filter(Invoice.invoice_id == invoice_id)
        .first()
    )

    if not invoice:
        return RedirectResponse(
            "/invoices",
            status_code=303
        )

    # Delete all items belonging to this invoice first
    db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice_id
    ).delete(
        synchronize_session=False
    )

    # Delete the invoice itself
    db.delete(invoice)

    db.commit()

    return RedirectResponse(
        "/invoices",
        status_code=303
    )