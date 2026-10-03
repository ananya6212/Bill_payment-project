from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Item(Base):
    __tablename__ = "items"

    name = Column(String, primary_key=True, index=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=50)

    invoice_items = relationship(
        "InvoiceItem",
        back_populates="item"
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    invoice_id = Column(
        Integer,
        unique=True,
        nullable=False,
        index=True
    )

    customer_name = Column(
        String,
        nullable=False
    )

    date = Column(
        String,
        nullable=False
    )

    subtotal = Column(
        Float,
        nullable=False,
        default=0
    )

    discount = Column(
        Float,
        nullable=False,
        default=0
    )

    tax = Column(
        Float,
        nullable=False,
        default=0
    )

    total_amount = Column(
        Float,
        nullable=False
    )

    payment_mode = Column(
        String,
        nullable=False,
        default="Cash"
    )

    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.invoice_id"),
        nullable=False
    )

    item_name = Column(
        String,
        ForeignKey("items.name"),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    invoice = relationship(
        "Invoice",
        back_populates="items"
    )

    item = relationship(
        "Item",
        back_populates="invoice_items"
    )

class Setting(Base):
    __tablename__ = "settings"

    key = Column(
        String,
        primary_key=True
    )

    value = Column(
        String,
        nullable=False
    )