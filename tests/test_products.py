"""Integration tests for the product catalog routes.

Reads (GET) are public; writes (POST / PUT / DELETE) are admin-only. The French
URLs come from the spec; the JSON payloads stay in English.
"""

import pytest

from app import db
from app.models import Product

VALID_PRODUCT = {
    "name": "Clavier mécanique",
    "description": "Clavier mécanique RGB, switches rouges",
    "category": "Périphériques",
    "price": 89.99,
    "stock": 25,
}


@pytest.fixture
def make_product(app):
    """Insert a product straight into the DB, bypassing the API."""

    def _make(**overrides):
        product = Product(**{**VALID_PRODUCT, **overrides})
        db.session.add(product)
        db.session.commit()
        return product

    return _make


# --- GET /api/produits (public) ---------------------------------------------


def test_list_products_is_public(client, make_product):
    make_product(name="Clavier mécanique")
    make_product(name="Souris gaming")

    # No token needed: anyone can browse the catalog.
    resp = client.get("/api/produits")
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, list)
    assert {p["name"] for p in body} == {"Clavier mécanique", "Souris gaming"}


def test_list_products_is_empty_without_data(client):
    resp = client.get("/api/produits")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_product_returns_its_full_details(client, make_product):
    product = make_product()

    resp = client.get(f"/api/produits/{product.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    # The detailed fiche carries every field the spec lists.
    assert body["id"] == product.id
    assert body["name"] == VALID_PRODUCT["name"]
    assert body["description"] == VALID_PRODUCT["description"]
    assert body["category"] == VALID_PRODUCT["category"]
    assert body["price"] == pytest.approx(VALID_PRODUCT["price"])
    assert body["stock"] == VALID_PRODUCT["stock"]


def test_get_unknown_product_returns_404(client):
    resp = client.get("/api/produits/999999")
    assert resp.status_code == 404


def test_search_filters_products_by_name(client, make_product):
    # Distinct descriptions so the match can only come from the name.
    make_product(name="Clavier mécanique", description="RGB keyboard")
    make_product(name="Souris gaming", description="Wireless mouse")

    # Search is a partial, case-insensitive match.
    resp = client.get("/api/produits?search=clavier")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()]
    assert names == ["Clavier mécanique"]


# --- POST /api/produits (admin only) ----------------------------------------


def test_admin_creates_a_product(client, admin_header):
    resp = client.post("/api/produits", json=VALID_PRODUCT, headers=admin_header)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == VALID_PRODUCT["name"]
    assert body["price"] == pytest.approx(VALID_PRODUCT["price"])
    assert body["stock"] == VALID_PRODUCT["stock"]
    assert "id" in body

    # It is really persisted and visible to everyone afterwards.
    listing = client.get("/api/produits").get_json()
    assert any(p["id"] == body["id"] for p in listing)


def test_create_product_requires_authentication(client):
    # No token at all: the endpoint is not open to anonymous callers.
    resp = client.post("/api/produits", json=VALID_PRODUCT)
    assert resp.status_code == 401


def test_create_product_is_forbidden_for_clients(client, client_header):
    # Authenticated but not an admin: forbidden.
    resp = client.post("/api/produits", json=VALID_PRODUCT, headers=client_header)
    assert resp.status_code == 403


def test_create_product_rejects_a_missing_field(client, admin_header):
    incomplete = {k: v for k, v in VALID_PRODUCT.items() if k != "name"}
    resp = client.post("/api/produits", json=incomplete, headers=admin_header)
    assert resp.status_code == 400


def test_create_product_rejects_a_negative_price(client, admin_header):
    # A negative price is nonsense and must be refused.
    resp = client.post(
        "/api/produits", json={**VALID_PRODUCT, "price": -5}, headers=admin_header
    )
    assert resp.status_code == 400


# --- PUT /api/produits/{id} (admin only) ------------------------------------


def test_admin_updates_a_product(client, admin_header, make_product):
    product = make_product(price=50.0, stock=10)

    resp = client.put(
        f"/api/produits/{product.id}",
        json={**VALID_PRODUCT, "price": 120.0, "stock": 3},
        headers=admin_header,
    )
    assert resp.status_code == 200

    # The change is persisted, including the stock (stock management).
    refreshed = client.get(f"/api/produits/{product.id}").get_json()
    assert refreshed["price"] == pytest.approx(120.0)
    assert refreshed["stock"] == 3


def test_update_unknown_product_returns_404(client, admin_header):
    resp = client.put("/api/produits/999999", json=VALID_PRODUCT, headers=admin_header)
    assert resp.status_code == 404


def test_update_product_is_forbidden_for_clients(client, client_header, make_product):
    product = make_product()
    resp = client.put(
        f"/api/produits/{product.id}", json=VALID_PRODUCT, headers=client_header
    )
    assert resp.status_code == 403


# --- DELETE /api/produits/{id} (admin only) ---------------------------------


def test_admin_deletes_a_product(client, admin_header, make_product):
    product = make_product()

    resp = client.delete(f"/api/produits/{product.id}", headers=admin_header)
    assert resp.status_code == 204

    # Gone for good.
    assert client.get(f"/api/produits/{product.id}").status_code == 404


def test_delete_unknown_product_returns_404(client, admin_header):
    resp = client.delete("/api/produits/999999", headers=admin_header)
    assert resp.status_code == 404


def test_delete_product_requires_authentication(client, make_product):
    product = make_product()
    resp = client.delete(f"/api/produits/{product.id}")
    assert resp.status_code == 401


def test_delete_product_is_forbidden_for_clients(client, client_header, make_product):
    product = make_product()
    resp = client.delete(f"/api/produits/{product.id}", headers=client_header)
    assert resp.status_code == 403
