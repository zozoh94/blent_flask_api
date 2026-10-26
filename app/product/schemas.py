from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    created_at: datetime


class ProductDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    description: str
    price: float
    stock: int
    created_at: datetime
