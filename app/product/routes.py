from flask import Blueprint, request

from app.extensions import db
from app.models import Product

from .schemas import ProductDetailOut, ProductListOut

bp = Blueprint("product", __name__)

SORTABLE = {
    "name": Product.name,
    "price": Product.price,
    "stock": Product.stock,
    "created_at": Product.created_at,
}


@bp.get("")
def get_products():
    """List products"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "asc")
    column = SORTABLE.get(sort, Product.created_at)
    column = column.desc() if order == "desc" else column.asc()
    search = request.args.get("search")

    query = db.select(Product)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    query = query.order_by(column)

    pagination = db.paginate(
        query, page=page, per_page=per_page, max_per_page=100, error_out=False
    )

    return {
        "items": [
            ProductListOut.model_validate(p).model_dump() for p in pagination.items
        ],
        "page": pagination.page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }


@bp.get("<id>")
def get_product(id: int):
    """Get a product by ID"""
    product = db.get_or_404(Product, id)
    return ProductDetailOut.model_validate(product).model_dump()
