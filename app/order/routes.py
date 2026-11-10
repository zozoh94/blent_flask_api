from flask import Blueprint, abort, request
from flask_jwt_extended import current_user, jwt_required
from pydantic import ValidationError
from spectree import Response

from app.auth.decorators import admin_required
from app.extensions import BEARER, api, db
from app.models import Order, OrderItem, Product

from .schemas import OrderCreate, OrderItemOut, OrderOut, OrderUpdate
from .service import IllegalStatusTransition, InsufficientStock, set_order_status

bp = Blueprint("order", __name__)


def _order_for_current_user(order_id):
    """Load an order the caller may see, or 404.
    Non-owners get 404 (not 403) so they cannot tell the order exists.
    """
    desc = "Order not found"
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404, description=desc)
    if current_user.role != "admin" and order.user_id != current_user.id:
        abort(404, description=desc)
    return order


@bp.get("")
@api.validate(
    resp=Response("HTTP_200", "HTTP_401"),
    tags=["orders"],
    security=BEARER,
    skip_validation=True,
)
@jwt_required()
def get_orders():
    """List orders"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    order = request.args.get("order", "desc")
    column = Order.created_at
    column = column.asc() if order == "asc" else column.desc()

    query = db.select(Order)
    if current_user.role == "admin":
        user_id = request.args.get("user_id", None, type=int)
    else:
        user_id = current_user.id

    if user_id:
        query = query.where(Order.user_id == user_id)

    query = query.order_by(column)

    pagination = db.paginate(
        query, page=page, per_page=per_page, max_per_page=100, error_out=False
    )

    return {
        "items": [OrderOut.model_validate(o).model_dump() for o in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }


@bp.get("<id>")
@api.validate(
    resp=Response("HTTP_401", "HTTP_404", HTTP_200=OrderOut),
    tags=["orders"],
    security=BEARER,
    skip_validation=True,
)
@jwt_required()
def get_order(id: int):
    """Get an order by ID"""
    order = _order_for_current_user(id)
    return OrderOut.model_validate(order).model_dump()


@bp.post("")
@api.validate(
    json=OrderCreate,
    resp=Response("HTTP_400", "HTTP_401", HTTP_201=OrderOut),
    tags=["orders"],
    security=BEARER,
    skip_validation=True,
)
@jwt_required()
def create_order():
    """Create an order"""
    try:
        data = OrderCreate.model_validate(request.get_json())
    except ValidationError as e:
        abort(400, str(e))

    items = []
    for item in data.items:
        product = db.session.get(Product, item.product_id)
        if product is None:
            abort(400, description=f"Product {id} not found")

        items.append(
            OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,  # snapshot du prix
            )
        )

    order = Order(
        user_id=current_user.id,
        shipping_address=data.shipping_address,
        items=items,
    )
    db.session.add(order)
    db.session.commit()
    return OrderOut.model_validate(order).model_dump(), 201


@bp.patch("<id>")
@api.validate(
    json=OrderUpdate,
    resp=Response(
        "HTTP_400", "HTTP_401", "HTTP_403", "HTTP_404", "HTTP_409", HTTP_200=OrderOut
    ),
    tags=["orders"],
    security=BEARER,
    skip_validation=True,
)
@admin_required
def update_order(id: int):
    """Update an order by ID (only status)"""
    order = _order_for_current_user(id)

    try:
        data = OrderUpdate.model_validate(request.get_json())
    except ValidationError as e:
        abort(400, str(e))

    try:
        set_order_status(order, data.status)
    except (InsufficientStock, IllegalStatusTransition) as e:
        abort(409, str(e))

    db.session.commit()
    return OrderOut.model_validate(order).model_dump()


@bp.get("<id>/items")
@api.validate(
    resp=Response("HTTP_200", "HTTP_401", "HTTP_404"),
    tags=["orders"],
    security=BEARER,
    skip_validation=True,
)
@jwt_required()
def get_order_items(id: int):
    """List order items"""
    order = _order_for_current_user(id)
    return [OrderItemOut.model_validate(item).model_dump() for item in order.items]
