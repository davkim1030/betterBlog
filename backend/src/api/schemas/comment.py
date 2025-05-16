from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    """댓글 기본 스키마"""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[UUID] = None


class CommentCreate(CommentBase):
    """댓글 생성 요청 스키마"""
    pass


class CommentUpdate(BaseModel):
    """댓글 수정 요청 스키마"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(CommentBase):
    """댓글 응답 스키마"""
    id: UUID
    post_id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_edited: bool
    like_count: int
    reply_count: int = 0

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """댓글 목록 응답 스키마"""
    items: List[CommentResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class CommentStats(BaseModel):
    """댓글 통계 응답 스키마"""
    total_comments: int
    total_root_comments: int
    total_replies: int
    total_likes: int
    comments_by_hour: dict[int, int]  # 시간대별 댓글 수
    most_active_commenters: List[tuple[UUID, int]]  # 가장 활발한 댓글 작성자
    most_liked_comments: List[CommentResponse]  # 가장 많은 좋아요를 받은 댓글
    most_replied_comments: List[tuple[CommentResponse, int]]  # 가장 많은 답글을 받은 댓글 