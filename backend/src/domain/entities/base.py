from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = uuid4()
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()
        super().__init__(**data)

    def update(self):
        self.updated_at = datetime.utcnow()
 