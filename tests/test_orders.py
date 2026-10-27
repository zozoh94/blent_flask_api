"""Integration tests for the order management routes.

Clients place and track their own orders; admins see everything and move an
order through its statuses. Stock is only touched when an order is validated.
"""

import pytest

from app import db
from app.models import Product

SHIPPING = "12 rue de la Paix, Paris"


@pytest.fixture
def make_product(app):
    """Insert a product with a known price and stock."""

    def _make(price=10.0, stock=100, **overrides):
        data = {
            "name": "Widget",
            "description": "A widget",
            "category": "Misc",
            "price": price,
            "stock": stock,
            **overrides,
        }
        product = Product(**data)
        db.session.add(product)
        db.session.commit()
        return product

    return _make


def _place_order(client, header, product_id, quantity=1, address=SHIPPING):
    """Place a single-line order as the holder of `header`."""
    return client.post(
        "/api/orders",
        json={
            "shipping_address": address,
            "items": [{"product_id": product_id, "quantity": quantity}],
        },
        headers=header,
    )


# --- POST /api/orders (authenticated client) --------------------------------


def test_client_creates_an_order(client, client_header, make_product):
    product = make_product()

    resp = _place_order(client, client_header, product.id, quantity=2)
    assert resp.status_code == 201
    body = resp.get_json()
    assert "id" in body
    # A brand new order waits for the admin: it starts pending.
    assert body["status"] == "pending"
    assert body["shipping_address"] == SHIPPING


def test_create_order_requires_authentication(client, make_product):
    product = make_product()
    resp = _place_order(client, {}, product.id)  # no Authorization header
    assert resp.status_code == 401


def test_create_order_rejects_empty_items(client, client_header):
    # An order with nothing in it is meaningless.
    resp = client.post(
        "/api/orders",
        json={"shipping_address": SHIPPING, "items": []},
        headers=client_header,
    )
    assert resp.status_code == 400


def test_create_order_rejects_an_unknown_product(client, client_header):
    resp = _place_order(client, client_header, 999999, quantity=1)
    assert resp.status_code == 400


def test_order_captures_the_price_at_creation_time(
    client, client_header, admin_header, make_product
):
    product = make_product(price=10.0, stock=100)
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    # The admin later raises the catalog price.
    client.put(
        f"/api/products/{product.id}",
        json={
            "name": "Widget",
            "description": "A widget",
            "category": "Misc",
            "price": 20.0,
            "stock": 100,
        },
        headers=admin_header,
    )

    # The order item keeps the price as it was when the order was placed.
    items = client.get(
        f"/api/orders/{order_id}/items", headers=client_header
    ).get_json()
    assert items[0]["unit_price"] == pytest.approx(10.0)


# --- GET /api/orders (admin sees all, client sees own) ----------------------


def test_client_sees_only_their_own_orders(client, auth_header_factory, make_product):
    product = make_product()
    alice = auth_header_factory(role="client")
    bob = auth_header_factory(role="client")
    order_a = _place_order(client, alice, product.id).get_json()["id"]
    order_b = _place_order(client, bob, product.id).get_json()["id"]

    ids = [o["id"] for o in client.get("/api/orders", headers=alice).get_json()]
    assert order_a in ids
    assert order_b not in ids


def test_admin_sees_every_order(
    client, auth_header_factory, admin_header, make_product
):
    product = make_product()
    alice = auth_header_factory(role="client")
    bob = auth_header_factory(role="client")
    order_a = _place_order(client, alice, product.id).get_json()["id"]
    order_b = _place_order(client, bob, product.id).get_json()["id"]

    ids = [o["id"] for o in client.get("/api/orders", headers=admin_header).get_json()]
    assert {order_a, order_b} <= set(ids)


def test_list_orders_requires_authentication(client):
    assert client.get("/api/orders").status_code == 401


# --- GET /api/orders/<id> ---------------------------------------------------


def test_client_gets_their_own_order(client, client_header, make_product):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    resp = client.get(f"/api/orders/{order_id}", headers=client_header)
    assert resp.status_code == 200
    assert resp.get_json()["id"] == order_id


def test_client_cannot_get_another_clients_order(
    client, auth_header_factory, make_product
):
    product = make_product()
    alice = auth_header_factory(role="client")
    bob = auth_header_factory(role="client")
    order_id = _place_order(client, alice, product.id).get_json()["id"]

    # Bob must not even learn the order exists.
    assert client.get(f"/api/orders/{order_id}", headers=bob).status_code == 404


def test_admin_gets_any_order(client, client_header, admin_header, make_product):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    assert (
        client.get(f"/api/orders/{order_id}", headers=admin_header).status_code == 200
    )


def test_get_unknown_order_returns_404(client, admin_header):
    assert client.get("/api/orders/999999", headers=admin_header).status_code == 404


# --- PATCH /api/orders/<id> (admin only) ------------------------------------


def test_admin_updates_the_order_status(
    client, client_header, admin_header, make_product
):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    resp = client.patch(
        f"/api/orders/{order_id}", json={"status": "shipped"}, headers=admin_header
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "shipped"


def test_patch_order_is_forbidden_for_clients(client, client_header, make_product):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    # Even on their own order, a client cannot change the status.
    resp = client.patch(
        f"/api/orders/{order_id}", json={"status": "shipped"}, headers=client_header
    )
    assert resp.status_code == 403


def test_patch_order_requires_authentication(client, client_header, make_product):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]
    assert (
        client.patch(f"/api/orders/{order_id}", json={"status": "shipped"}).status_code
        == 401
    )


def test_patch_order_rejects_an_invalid_status(
    client, client_header, admin_header, make_product
):
    product = make_product()
    order_id = _place_order(client, client_header, product.id).get_json()["id"]

    resp = client.patch(
        f"/api/orders/{order_id}", json={"status": "bogus"}, headers=admin_header
    )
    assert resp.status_code == 400


def test_patch_unknown_order_returns_404(client, admin_header):
    resp = client.patch(
        "/api/orders/999999", json={"status": "shipped"}, headers=admin_header
    )
    assert resp.status_code == 404


# --- Stock is enforced on validation ----------------------------------------


def test_validating_an_order_decrements_stock(
    client, client_header, admin_header, make_product
):
    product = make_product(stock=10)
    order_id = _place_order(client, client_header, product.id, quantity=3).get_json()[
        "id"
    ]

    resp = client.patch(
        f"/api/orders/{order_id}", json={"status": "validated"}, headers=admin_header
    )
    assert resp.status_code == 200

    # The 3 ordered units are gone from the catalog stock.
    stock = client.get(f"/api/products/{product.id}").get_json()["stock"]
    assert stock == 7


def test_validating_with_insufficient_stock_is_rejected(
    client, client_header, admin_header, make_product
):
    product = make_product(stock=2)
    order_id = _place_order(client, client_header, product.id, quantity=5).get_json()[
        "id"
    ]

    resp = client.patch(
        f"/api/orders/{order_id}", json={"status": "validated"}, headers=admin_header
    )
    # Not enough stock: the validation is refused.
    assert resp.status_code == 409

    # Nothing changed: stock is intact and the order is not validated.
    assert client.get(f"/api/products/{product.id}").get_json()["stock"] == 2
    order = client.get(f"/api/orders/{order_id}", headers=admin_header).get_json()
    assert order["status"] != "validated"


# --- GET /api/orders/<id>/items ---------------------------------------------


def test_order_items_list_the_ordered_products(client, client_header, make_product):
    product = make_product(price=15.0)
    order_id = _place_order(client, client_header, product.id, quantity=4).get_json()[
        "id"
    ]

    resp = client.get(f"/api/orders/{order_id}/items", headers=client_header)
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]["product_id"] == product.id
    assert items[0]["quantity"] == 4
    assert items[0]["unit_price"] == pytest.approx(15.0)


def test_client_cannot_see_another_clients_order_items(
    client, auth_header_factory, make_product
):
    product = make_product()
    alice = auth_header_factory(role="client")
    bob = auth_header_factory(role="client")
    order_id = _place_order(client, alice, product.id).get_json()["id"]

    assert client.get(f"/api/orders/{order_id}/items", headers=bob).status_code == 404
