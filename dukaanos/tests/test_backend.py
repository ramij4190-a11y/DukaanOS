"""Automated Integration Test Suite for DukaanOS Backend & Multi-Tenant API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dukaanos.src.dukaanos.backend.database import Base, get_db
from dukaanos.src.dukaanos.backend.main import app

# Create in-memory SQLite database for isolated test execution
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def client():
    """Sets up a fresh in-memory database and FastAPI test client."""
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


def test_health_check(client):
    """Verifies service health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_store_registration_and_login(client):
    """Tests tenant registration and JWT token issuance."""
    # Register Store A
    res_reg = client.post(
        "/api/v1/auth/register-store",
        params={"owner_username": "ramesh_owner", "owner_password": "securepassword123"},
        json={
            "id": "STORE-001",
            "name": "Shree Ganesh Kirana",
            "owner_name": "Ramesh Kumar",
            "phone": "9876543210",
            "city": "Delhi",
        },
    )
    assert res_reg.status_code == 200
    store_data = res_reg.json()
    assert store_data["id"] == "STORE-001"

    # Login to obtain JWT
    res_login = client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh_owner", "password": "securepassword123"},
    )
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["store_id"] == "STORE-001"


def test_multi_tenant_isolation(client):
    """Challenge 05: Store B must never access or view Store A's catalog or ledger."""
    # Login Store A
    token_a = client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh_owner", "password": "securepassword123"},
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Store A creates a product
    client.post(
        "/api/v1/products",
        headers=headers_a,
        params={"initial_stock": 50},
        json={
            "sku": "STP-001",
            "name": "Aashirvaad Atta 5kg",
            "category": "Staples & Grains",
            "cost_price": 225.0,
            "selling_price": 245.0,
            "min_reorder_level": 20,
        },
    )

    # Register Store B
    client.post(
        "/api/v1/auth/register-store",
        params={"owner_username": "suresh_owner", "owner_password": "sureshpassword123"},
        json={
            "id": "STORE-002",
            "name": "MahaLaxmi Provision Store",
            "owner_name": "Suresh Patel",
            "phone": "9811223344",
            "city": "Ahmedabad",
        },
    )
    token_b = client.post(
        "/api/v1/auth/login",
        data={"username": "suresh_owner", "password": "sureshpassword123"},
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Store B queries products -> Must be empty!
    res_b = client.get("/api/v1/products", headers=headers_b)
    assert res_b.status_code == 200
    assert len(res_b.json()) == 0  # Multi-tenant isolation verified!


def test_sales_checkout_and_idempotency(client):
    """Challenge 03: Idempotent checkout prevents double-deductions."""
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh_owner", "password": "securepassword123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get product id
    prods = client.get("/api/v1/products", headers=headers).json()
    prod_id = prods[0]["id"]
    initial_stock = prods[0]["current_stock"]  # 50

    # Execute checkout with Idempotency-Key
    checkout_payload = {
        "payment_method": "UPI",
        "items": [{"product_id": prod_id, "quantity": 3}],
        "idempotency_key": "IDEMP-TX-UNIQUE-999",
    }

    res1 = client.post(
        "/api/v1/sales",
        headers={**headers, "Idempotency-Key": "IDEMP-TX-UNIQUE-999"},
        json=checkout_payload,
    )
    assert res1.status_code == 200
    tx1 = res1.json()
    invoice1 = tx1["invoice_id"]

    # Re-submit the exact same checkout with same idempotency key (e.g. network retry)
    res2 = client.post(
        "/api/v1/sales",
        headers={**headers, "Idempotency-Key": "IDEMP-TX-UNIQUE-999"},
        json=checkout_payload,
    )
    assert res2.status_code == 200
    tx2 = res2.json()
    assert tx2["invoice_id"] == invoice1  # Same invoice returned!

    # Verify inventory was ONLY deducted once (50 - 3 = 47)
    updated_prod = client.get("/api/v1/products", headers=headers).json()[0]
    assert updated_prod["current_stock"] == initial_stock - 3


def test_purchase_order_lifecycle_into_ledger(client):
    """Verifies that receiving an approved PO adds stock into the inventory ledger."""
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh_owner", "password": "securepassword123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prod = client.get("/api/v1/products", headers=headers).json()[0]
    stock_before = prod["current_stock"]

    # 1. Draft PO
    res_draft = client.post(
        "/api/v1/purchase-orders",
        headers=headers,
        json={
            "supplier_name": "Shree Ganesh Grain Mandi",
            "items": [{"product_id": prod["id"], "quantity_ordered": 20, "unit_cost": 225.0}],
        },
    )
    assert res_draft.status_code == 200
    po_id = res_draft.json()["id"]
    assert res_draft.json()["status"] == "DRAFT"

    # 2. Approve PO
    res_approve = client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=headers)
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "APPROVED"

    # 3. Receive PO into stock
    res_receive = client.post(f"/api/v1/purchase-orders/{po_id}/receive", headers=headers)
    assert res_receive.status_code == 200
    assert res_receive.json()["status"] == "RECEIVED"

    # Verify ledger updated stock (+20)
    stock_after = client.get("/api/v1/products", headers=headers).json()[0]["current_stock"]
    assert stock_after == stock_before + 20


def test_daily_brief_intelligence(client):
    """Verifies morning intelligence brief calculations."""
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "ramesh_owner", "password": "securepassword123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/intelligence/daily-brief", headers=headers)
    assert res.status_code == 200
    brief = res.json()
    assert "predicted_sales_inr" in brief
    assert brief["predicted_sales_inr"] > 0
    assert "purchase_suggestions" in brief
    assert isinstance(brief["purchase_suggestions"], list)

