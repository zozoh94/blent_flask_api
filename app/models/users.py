from datetime import UTC, datetime

from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    role: Mapped[str] = mapped_column(default="client")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    _password_hash: Mapped[str] = mapped_column("password_hash")

    @property
    def password(self) -> str:
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, raw_password: str) -> None:
        self._password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self._password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
        }
