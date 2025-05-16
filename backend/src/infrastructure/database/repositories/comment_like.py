from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.comment_like import CommentLike
from src.domain.repositories.comment_like import CommentLikeRepository
from src.infrastructure.database.models.comment_like import CommentLike as CommentLikeModel
from .base import SQLAlchemyRepository


class SQLAlchemyCommentLikeRepository(SQLAlchemyRepository[CommentLikeModel, CommentLike], CommentLikeRepository):
    """SQLAlchemy를 사용하는 댓글 좋아요 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CommentLikeModel, CommentLike)

    async def get_by_user_and_comment(
        self, user_id: UUID, comment_id: UUID
    ) -> Optional[CommentLike]:
        """사용자와 댓글로 좋아요를 조회합니다."""
        query = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.comment_id == comment_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self.entity_class.model_validate(model) if model else None

    async def get_by_comment_id(
        self, comment_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[CommentLike]:
        """댓글의 좋아요 목록을 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.comment_id == comment_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[CommentLike]:
        """사용자의 좋아요 목록을 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def delete_by_user_and_comment(
        self, user_id: UUID, comment_id: UUID
    ) -> bool:
        """사용자와 댓글로 좋아요를 삭제합니다."""
        query = delete(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.comment_id == comment_id,
        )
        result = await self.session.execute(query)
        return result.rowcount > 0 