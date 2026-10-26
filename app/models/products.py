from datetime import UTC, datetime

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str]
    price: Mapped[float]
    stock: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
