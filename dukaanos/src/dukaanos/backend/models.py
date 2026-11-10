"""Multi-Tenant Domain Models for DukaanOS Retail Platform.

Implements:
- Store (Tenant context)
- User (RBAC: Owner, Clerk)
- Product (Catalog & Pricing)
- InventoryLedger (Event-sourced immutable stock tracking)
- SalesTransaction & SalesItem (Counter sales with Idempotency protection)
- PurchaseOrder & PurchaseOrderItem (Procurement workflow)
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from dukaanos.src.dukaanos.backend.database import Base


class Store(Base):
    """Retail store tenant entity."""
    __tablename__ = "stores"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "STORE-001"
    name = Column(String(150), nullable=False)
    owner_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="store", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    ledger_entries = relationship("InventoryLedger", back_populates="store", cascade="all, delete-orphan")
    sales = relationship("SalesTransaction", back_populates="store", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="store", cascade="all, delete-orphan")


class User(Base):
    """Store staff / owner user model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(50), ForeignKey("stores.id"), nullable=False, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="CLERK")  # "OWNER", "CLERK", "ADMIN"
    created_at = Column(DateTime, default=datetime.utcnow)

    store = relationship("Store", back_populates="users")


class Product(Base):
    """Product Master Catalog for each retail store."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(50), ForeignKey("stores.id"), nullable=False, index=True)
    sku = Column(String(50), nullable=False, index=True)  # e.g. "STP-001"
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    unit = Column(String(50), default="Piece")
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    min_reorder_level = Column(Integer, default=15)
    lead_time_days = Column(Integer, default=2)
    supplier_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True)

    store = relationship("Store", back_populates="products")
    ledger_entries = relationship("InventoryLedger", back_populates="product")

    __table_args__ = (
        Index("idx_store_sku", "store_id", "sku", unique=True),
    )


class InventoryLedger(Base):
    """Event-sourced append-only inventory ledger. Every change is an atomic event."""
    __tablename__ = "inventory_ledger"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(50), ForeignKey("stores.id"), nullable=False, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)  # "TX-000001"
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # "OPENING_STOCK", "PURCHASE", "SALE", "DAMAGE_EXPIRED", "RETURN"
    quantity_change = Column(Integer, nullable=False)  # Positive (add) or negative (deduct)
    running_balance = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    reference_id = Column(String(100), nullable=True)  # e.g. Invoice #, PO #
    notes = Column(Text, nullable=True)

    store = relationship("Store", back_populates="ledger_entries")
    product = relationship("Product", back_populates="ledger_entries")


class SalesTransaction(Base):
    """Sales invoice header with idempotency key."""
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(50), ForeignKey("stores.id"), nullable=False, index=True)
    invoice_id = Column(String(50), unique=True, index=True, nullable=False)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)  # Prevents duplicate charges
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    payment_method = Column(String(50), default="CASH")  # "UPI", "CASH", "KHATA_CREDIT"
    total_revenue = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    gross_profit = Column(Float, nullable=False, default=0.0)

    store = relationship("Store", back_populates="sales")
    items = relationship("SalesItem", back_populates="transaction", cascade="all, delete-orphan")


class SalesItem(Base):
    """Line items inside a sales transaction."""
    __tablename__ = "sales_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("sales_transactions.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    transaction = relationship("SalesTransaction", back_populates="items")
    product = relationship("Product")


class PurchaseOrder(Base):
    """Supplier procurement purchase orders."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String(50), ForeignKey("stores.id"), nullable=False, index=True)
    po_number = Column(String(50), unique=True, index=True, nullable=False)  # "PO-000001"
    supplier_name = Column(String(150), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expected_delivery_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="DRAFT")  # "DRAFT", "APPROVED", "RECEIVED", "CANCELLED"
    total_amount = Column(Float, default=0.0)

    store = relationship("Store", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """Line items inside a purchase order."""
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity_ordered = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")

