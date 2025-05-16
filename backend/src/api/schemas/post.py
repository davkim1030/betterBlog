from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.post import PostStatus


class PostBase(BaseModel):
    """포스트 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    featured_image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category_id: Optional[UUID] = None
    is_featured: bool = False
    allow_comments: bool = True


class PostCreate(PostBase):
    """포스트 생성 요청 스키마"""
    status: PostStatus = PostStatus.DRAFT


class PostUpdate(PostBase):
    """포스트 수정 요청 스키마"""
    status: Optional[PostStatus] = None


class PostResponse(PostBase):
    """포스트 응답 스키마"""
    id: UUID
    author_id: UUID
    status: PostStatus
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """포스트 목록 응답 스키마"""
    items: List[PostResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class PostStats(BaseModel):
    """포스트 통계 응답 스키마"""
    total_posts: int
    total_views: int
    total_likes: int
    total_comments: int
    posts_by_status: dict[PostStatus, int]
    posts_by_category: dict[UUID, int]
    popular_tags: List[tuple[str, int]] 