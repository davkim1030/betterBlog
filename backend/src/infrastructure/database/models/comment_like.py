from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CommentLike(BaseModel):
    """댓글 좋아요 모델"""
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "comment_id",
            name="uq_comment_likes_user_comment"
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    comment_id: Mapped[UUID] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ) 