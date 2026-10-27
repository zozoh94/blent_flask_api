from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    category: str
    description: str | None = None
    price: float = Field(ge=0)
    stock: int = Field(ge=0)


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
