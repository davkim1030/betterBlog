from typing import Optional
from uuid import UUID

from .base import Entity


class Category(Entity):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    order: int = 0
    
    def update_order(self, new_order: int):
        self.order = new_order
        self.update() 
