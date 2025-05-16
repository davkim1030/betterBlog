from typing import Optional
from uuid import UUID

from .base import Entity


class Comment(Entity):
    content: str
    author_id: UUID
    post_id: UUID
    parent_id: Optional[UUID] = None
    is_edited: bool = False
    like_count: int = 0
    
    def edit(self, new_content: str):
        self.content = new_content
        self.is_edited = True
        self.update()
    
    def increment_like(self):
        self.like_count += 1
    
    def decrement_like(self):
        if self.like_count > 0:
            self.like_count -= 1 
