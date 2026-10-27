from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.auth.decorators import admin_required
from app.extensions import db
from app.models import Product

from .schemas import (
    ProductCreate,
    ProductDetailOut,
    ProductListOut,
)

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


@bp.post("")
@admin_required
def create_product():
    """Create a product"""
    try:
        data = ProductCreate.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    product = Product(**data.model_dump())
    db.session.add(product)
    db.session.commit()
    return ProductDetailOut.model_validate(product).model_dump(mode="json"), 201


@bp.put("<id>")
@admin_required
def update_product(id: int):
    """Update a product"""
    product = db.get_or_404(Product, id)
    data = ProductCreate.model_validate(request.get_json())
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    db.session.commit()
    return ProductDetailOut.model_validate(product).model_dump()


@bp.delete("<id>")
@admin_required
def delete_product(id: int):
    """Delete a product"""
    product = db.get_or_404(Product, id)
    db.session.delete(product)
    db.session.commit()
    return "", 204
