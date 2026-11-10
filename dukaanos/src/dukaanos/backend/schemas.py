"""Pydantic v2 Request and Response Schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# 1. Authentication
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    store_id: str
    username: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    store_id: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# 2. Store
class StoreCreate(BaseModel):
    id: str = Field(..., example="STORE-001")
    name: str = Field(..., example="Shree Ganesh Kirana Store")
    owner_name: str = Field(..., example="Ramesh Kumar")
    phone: Optional[str] = "9876543210"
    city: Optional[str] = "Delhi"


class StoreOut(StoreCreate):
    created_at: datetime

    class Config:
        from_attributes = True


# 3. Product Catalog
class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    unit: str = "Piece"
    cost_price: float
    selling_price: float
    min_reorder_level: int = 15
    lead_time_days: int = 2
    supplier_name: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int
    store_id: str
    is_active: bool

    class Config:
        from_attributes = True


class ProductStockOut(ProductOut):
    current_stock: int
    reorder_point: int
    stock_status: str  # "OK", "LOW_STOCK", "OUT_OF_STOCK"


# 4. Inventory Ledger
class LedgerEntryOut(BaseModel):
    id: int
    store_id: str
    transaction_id: str
    date: datetime
    product_id: int
    event_type: str
    quantity_change: int
    running_balance: int
    unit_cost: float
    reference_id: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ReconciliationRequest(BaseModel):
    product_id: int
    physical_count: int
    notes: Optional[str] = "Monthly physical stocktaking audit"


class ReconciliationOut(BaseModel):
    product_id: int
    previous_ledger_stock: int
    physical_count: int
    adjustment_applied: int
    transaction_id: str
    reconciled_at: datetime


# 5. Sales Transactions
class SalesItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class SalesCreate(BaseModel):
    payment_method: str = Field("CASH", example="UPI")
    items: List[SalesItemCreate]
    idempotency_key: Optional[str] = None


class SalesItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    cost_price: float
    line_total: float

    class Config:
        from_attributes = True


class SalesOut(BaseModel):
    id: int
    store_id: str
    invoice_id: str
    idempotency_key: Optional[str]
    date: datetime
    payment_method: str
    total_revenue: float
    total_cost: float
    gross_profit: float
    items: List[SalesItemOut]

    class Config:
        from_attributes = True


# 6. Purchase Orders
class POItemCreate(BaseModel):
    product_id: int
    quantity_ordered: int = Field(..., gt=0)
    unit_cost: float


class POCreate(BaseModel):
    supplier_name: str
    expected_delivery_date: Optional[datetime] = None
    items: List[POItemCreate]


class POItemOut(BaseModel):
    id: int
    product_id: int
    quantity_ordered: int
    unit_cost: float
    total_cost: float

    class Config:
        from_attributes = True


class POOut(BaseModel):
    id: int
    store_id: str
    po_number: str
    supplier_name: str
    order_date: datetime
    expected_delivery_date: Optional[datetime]
    received_date: Optional[datetime]
    status: str
    total_amount: float
    items: List[POItemOut]

    class Config:
        from_attributes = True


# 7. Intelligence & Daily Brief
class PurchaseSuggestionItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    supplier_name: Optional[str]
    current_stock: int
    reorder_point: int
    suggested_order_qty: int
    estimated_cost: float
    urgency: str  # "CRITICAL", "HIGH", "MEDIUM"


class DailyBriefResponse(BaseModel):
    store_id: str
    store_name: str
    date: str
    predicted_sales_inr: float
    predicted_basket_count: int
    low_stock_products_count: int
    out_of_stock_count: int
    unusual_sales_alerts: int
    purchase_suggestions: List[PurchaseSuggestionItem]
    top_selling_category: str

