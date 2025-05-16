from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_edited: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    like_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    # Relationships
    author = relationship("User", backref="comments")
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", backref="replies", remote_side=[id]) 