from enum import Enum
from typing import List, Optional
from uuid import UUID

from .base import Entity


class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Post(Entity):
    title: str
    content: str
    author_id: UUID
    status: PostStatus = PostStatus.DRAFT
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    tags: List[str] = []
    category_id: Optional[UUID] = None
    view_count: int = 0
    like_count: int = 0
    is_featured: bool = False
    allow_comments: bool = True
    
    def publish(self):
        self.status = PostStatus.PUBLISHED
        self.update()
    
    def archive(self):
        self.status = PostStatus.ARCHIVED
        self.update()
    
    def increment_view(self):
        self.view_count += 1
    
    def increment_like(self):
        self.like_count += 1
    
    def decrement_like(self):
        if self.like_count > 0:
            self.like_count -= 1
