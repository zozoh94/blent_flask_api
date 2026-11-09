from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    shipping_address: str
    status: str
    created_at: datetime
