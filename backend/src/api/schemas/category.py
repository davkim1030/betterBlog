from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """카테고리 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    order: int = 0


class CategoryCreate(CategoryBase):
    """카테고리 생성 요청 스키마"""
    pass


class CategoryUpdate(CategoryBase):
    """카테고리 수정 요청 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CategoryResponse(CategoryBase):
    """카테고리 응답 스키마"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    post_count: int = 0

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """카테고리 목록 응답 스키마"""
    items: List[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """카테고리 통계 응답 스키마"""
    total_categories: int
    total_posts: int
    total_views: int
    categories_by_depth: dict[int, int]  # depth별 카테고리 수
    most_active_categories: List[tuple[CategoryResponse, dict[str, int]]]  # 가장 활발한 카테고리 