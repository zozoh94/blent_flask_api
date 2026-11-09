from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.product.schemas import ProductListOut


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=1)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderUpdate(BaseModel):
    status: Literal["pending", "validated", "shipped", "cancelled"]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    shipping_address: str
    status: str
    created_at: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductListOut
    quantity: int
    unit_price: float
