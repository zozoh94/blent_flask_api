"""Integration tests for the product catalog routes.

Reads (GET) are public; writes (POST / PUT / DELETE) are admin-only.
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


# --- GET /api/products (public) ---------------------------------------------


def test_list_products_is_public(client, make_product):
    make_product(name="Clavier mécanique")
    make_product(name="Souris gaming")

    # No token needed: anyone can browse the catalog.
    resp = client.get("/api/products")
    assert resp.status_code == 200
    body = resp.get_json()
    assert {p["name"] for p in body["items"]} == {"Clavier mécanique", "Souris gaming"}


def test_list_products_is_empty_without_data(client):
    resp = client.get("/api/products")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["items"] == []
    assert body["total"] == 0


def test_get_product_returns_its_full_details(client, make_product):
    product = make_product()

    resp = client.get(f"/api/products/{product.id}")
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
    resp = client.get("/api/products/999999")
    assert resp.status_code == 404


def test_search_filters_products_by_name(client, make_product):
    # Distinct descriptions so the match can only come from the name.
    make_product(name="Clavier mécanique", description="RGB keyboard")
    make_product(name="Souris gaming", description="Wireless mouse")

    # Search is a partial, case-insensitive match.
    resp = client.get("/api/products?search=clavier")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["items"]]
    assert names == ["Clavier mécanique"]


def test_listing_is_paginated(client, make_product):
    make_product(name="A")
    make_product(name="B")
    make_product(name="C")

    # First page of two: two items, but the envelope reports the whole picture.
    first = client.get("/api/products?per_page=2&page=1").get_json()
    assert len(first["items"]) == 2
    assert first["total"] == 3
    assert first["pages"] == 2
    assert first["page"] == 1
    assert first["per_page"] == 2

    # The second page holds the remaining one.
    second = client.get("/api/products?per_page=2&page=2").get_json()
    assert len(second["items"]) == 1
    assert second["page"] == 2


# --- POST /api/products (admin only) ----------------------------------------


def test_admin_creates_a_product(client, admin_header):
    resp = client.post("/api/products", json=VALID_PRODUCT, headers=admin_header)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == VALID_PRODUCT["name"]
    assert body["price"] == pytest.approx(VALID_PRODUCT["price"])
    assert body["stock"] == VALID_PRODUCT["stock"]
    assert "id" in body

    # It is really persisted and visible to everyone afterwards.
    listing = client.get("/api/products").get_json()["items"]
    assert any(p["id"] == body["id"] for p in listing)


def test_create_product_requires_authentication(client):
    # No token at all: the endpoint is not open to anonymous callers.
    resp = client.post("/api/products", json=VALID_PRODUCT)
    assert resp.status_code == 401


def test_create_product_is_forbidden_for_clients(client, client_header):
    # Authenticated but not an admin: forbidden.
    resp = client.post("/api/products", json=VALID_PRODUCT, headers=client_header)
    assert resp.status_code == 403


def test_create_product_rejects_a_missing_field(client, admin_header):
    incomplete = {k: v for k, v in VALID_PRODUCT.items() if k != "name"}
    resp = client.post("/api/products", json=incomplete, headers=admin_header)
    assert resp.status_code == 400


def test_create_product_rejects_a_negative_price(client, admin_header):
    # A negative price is nonsense and must be refused.
    resp = client.post(
        "/api/products", json={**VALID_PRODUCT, "price": -5}, headers=admin_header
    )
    assert resp.status_code == 400


# --- PUT /api/products/{id} (admin only) ------------------------------------


def test_admin_updates_a_product(client, admin_header, make_product):
    product = make_product(price=50.0, stock=10)

    resp = client.put(
        f"/api/products/{product.id}",
        json={**VALID_PRODUCT, "price": 120.0, "stock": 3},
        headers=admin_header,
    )
    assert resp.status_code == 200

    # The change is persisted, including the stock (stock management).
    refreshed = client.get(f"/api/products/{product.id}").get_json()
    assert refreshed["price"] == pytest.approx(120.0)
    assert refreshed["stock"] == 3


def test_update_unknown_product_returns_404(client, admin_header):
    resp = client.put("/api/products/999999", json=VALID_PRODUCT, headers=admin_header)
    assert resp.status_code == 404


def test_update_product_is_forbidden_for_clients(client, client_header, make_product):
    product = make_product()
    resp = client.put(
        f"/api/products/{product.id}", json=VALID_PRODUCT, headers=client_header
    )
    assert resp.status_code == 403


# --- DELETE /api/products/{id} (admin only) ---------------------------------


def test_admin_deletes_a_product(client, admin_header, make_product):
    product = make_product()

    resp = client.delete(f"/api/products/{product.id}", headers=admin_header)
    assert resp.status_code == 204

    # Gone for good.
    assert client.get(f"/api/products/{product.id}").status_code == 404


def test_delete_unknown_product_returns_404(client, admin_header):
    resp = client.delete("/api/products/999999", headers=admin_header)
    assert resp.status_code == 404


def test_delete_product_requires_authentication(client, make_product):
    product = make_product()
    resp = client.delete(f"/api/products/{product.id}")
    assert resp.status_code == 401


def test_delete_product_is_forbidden_for_clients(client, client_header, make_product):
    product = make_product()
    resp = client.delete(f"/api/products/{product.id}", headers=client_header)
    assert resp.status_code == 403
