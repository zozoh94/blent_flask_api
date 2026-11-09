"""Unit tests for the order status-change domain logic.

The money rule of the project: an order holds reserved catalog stock exactly
while it is validated. Entering validation reserves stock, leaving validation
for a cancellation gives it back, and the whole thing is all-or-nothing. On top
of that the status graph is constrained: an order can only ship once it has been
validated. These tests pin that state machine on plain in-memory objects, with
no HTTP and no database, so the business logic is checked in isolation.

The service trusts that the status is a licit value (the route validates it
through the schema), so unknown statuses are not exercised here.
"""

import pytest

from app.models import Order, OrderItem, Product
from app.order.service import (
    IllegalStatusTransition,
    InsufficientStock,
    set_order_status,
)

SHIPPING = "12 rue de la Paix, Paris"


def _order(*lines, status="pending"):
    """Build a transient order from (stock, quantity) pairs, one item per pair.

    `stock` is the product's current catalog stock, so a validated order is set
    up with stock already reduced by its quantity, as the database would hold it.
    """
    items = []
    for stock, quantity in lines:
        product = Product(
            name="Widget",
            description="A widget",
            category="Misc",
            price=10.0,
            stock=stock,
        )
        items.append(OrderItem(product=product, quantity=quantity, unit_price=10.0))
    return Order(user_id=1, shipping_address=SHIPPING, status=status, items=items)


# --- Reserving stock on validation ------------------------------------------


def test_validating_reserves_each_items_stock():
    # A validated order reserves exactly what was ordered, item by item.
    order = _order((10, 3), (5, 2))

    set_order_status(order, "validated")

    assert order.status == "validated"
    assert order.items[0].product.stock == 7
    assert order.items[1].product.stock == 3


def test_validating_without_enough_stock_raises():
    # The catalog cannot promise what it does not have.
    order = _order((2, 5))

    with pytest.raises(InsufficientStock):
        set_order_status(order, "validated")

    # The refusal leaves the world as it was: stock intact, order not validated.
    assert order.items[0].product.stock == 2
    assert order.status != "validated"


def test_validation_is_atomic_across_items():
    # Why validation checks every item BEFORE decrementing any: the first item
    # has plenty, the second falls short. A naive decrement-as-you-go would
    # already have eaten the first item's stock before hitting the shortfall.
    order = _order((10, 3), (1, 5))

    with pytest.raises(InsufficientStock):
        set_order_status(order, "validated")

    # Nothing moved, not even the item that could have been served on its own.
    assert order.items[0].product.stock == 10
    assert order.items[1].product.stock == 1
    assert order.status != "validated"


def test_validating_an_already_validated_order_is_rejected():
    # Re-validating would reserve the stock a second time: forbidden, so the
    # count can never drift below what was really ordered.
    order = _order((7, 3), status="validated")

    with pytest.raises(IllegalStatusTransition):
        set_order_status(order, "validated")

    assert order.items[0].product.stock == 7


# --- Releasing stock on cancellation (reversibility) ------------------------


def test_cancelling_a_pending_order_keeps_stock():
    # A pending order never reserved anything, so cancelling it touches no stock.
    order = _order((10, 3))

    set_order_status(order, "cancelled")

    assert order.status == "cancelled"
    assert order.items[0].product.stock == 10


def test_cancelling_a_validated_order_restocks():
    # Cancelling a validated order must give its reserved units back to the
    # catalog, otherwise that stock leaks and stays unsellable forever.
    order = _order((7, 3), status="validated")

    set_order_status(order, "cancelled")

    assert order.status == "cancelled"
    assert order.items[0].product.stock == 10


def test_revalidating_a_cancelled_order_reserves_again():
    # Reversibility round trip: a cancelled order can be validated again, which
    # reserves its stock afresh.
    order = _order((10, 3), status="cancelled")

    set_order_status(order, "validated")

    assert order.status == "validated"
    assert order.items[0].product.stock == 7


# --- Shipping is only reachable from validation -----------------------------


def test_shipping_a_validated_order_keeps_its_reserved_stock():
    # Goods leave the warehouse but were already deducted at validation, so
    # shipping must not decrement a second time.
    order = _order((7, 3), status="validated")

    set_order_status(order, "shipped")

    assert order.status == "shipped"
    assert order.items[0].product.stock == 7


def test_shipping_is_rejected_unless_validated():
    # You cannot ship what was never validated.
    order = _order((10, 3))

    with pytest.raises(IllegalStatusTransition):
        set_order_status(order, "shipped")

    assert order.status == "pending"
    assert order.items[0].product.stock == 10
