from typing import List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.post import PostStatus
from .base import BaseModel


class Post(BaseModel):
    __tablename__ = "posts"

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[PostStatus] = mapped_column(
        default=PostStatus.DRAFT,
        nullable=False,
        index=True,
    )
    excerpt: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    featured_image: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    view_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    like_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    is_featured: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    allow_comments: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    author = relationship("User", backref="posts")
    category = relationship("Category", backref="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan") 