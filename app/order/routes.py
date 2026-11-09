from flask import Blueprint, request
from flask_jwt_extended import current_user, jwt_required

from app.extensions import db
from app.models import Order, User

from .schemas import OrderOut

bp = Blueprint("order", __name__)


@bp.get("")
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
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
