from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.comment import Comment
from src.domain.repositories.comment import CommentRepository
from src.infrastructure.database.models.comment import Comment as CommentModel
from .base import SQLAlchemyRepository


class SQLAlchemyCommentRepository(SQLAlchemyRepository[CommentModel, Comment], CommentRepository):
    """SQLAlchemy를 사용하는 댓글 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CommentModel, Comment)

    async def get_by_post_id(
        self, post_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """게시물 ID로 댓글을 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.post_id == post_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_author_id(
        self, author_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """작성자 ID로 댓글을 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.author_id == author_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_replies(
        self, parent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """상위 댓글의 답글을 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_root_comments(
        self, post_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """게시물의 최상위 댓글을 조회합니다."""
        query = (
            select(self.model_class)
            .where(
                self.model_class.post_id == post_id,
                self.model_class.parent_id.is_(None)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_comment_count_by_post(self, post_id: UUID) -> int:
        """게시물의 총 댓글 수를 조회합니다."""
        query = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.post_id == post_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_reply_count_by_comment(self, comment_id: UUID) -> int:
        """댓글의 답글 수를 조회합니다."""
        query = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.parent_id == comment_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_most_active_commenters(self, limit: int = 10) -> List[Tuple[UUID, int]]:
        """가장 활발한 댓글 작성자를 조회합니다."""
        query = (
            select(
                self.model_class.author_id,
                func.count().label("comment_count")
            )
            .group_by(self.model_class.author_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def get_most_commented_posts(self, limit: int = 10) -> List[Tuple[UUID, int]]:
        """댓글이 가장 많은 게시물을 조회합니다."""
        query = (
            select(
                self.model_class.post_id,
                func.count().label("comment_count")
            )
            .group_by(self.model_class.post_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def get_comment_stats_by_author(self, author_id: UUID) -> Dict[str, int]:
        """작성자의 댓글 통계를 조회합니다."""
        # 전체 댓글 수
        total_query = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.author_id == author_id)
        )
        total_result = await self.session.execute(total_query)
        total_comments = total_result.scalar_one()

        # 답글 수
        replies_query = (
            select(func.count())
            .select_from(self.model_class)
            .where(
                self.model_class.author_id == author_id,
                self.model_class.parent_id.isnot(None)
            )
        )
        replies_result = await self.session.execute(replies_query)
        total_replies = replies_result.scalar_one()

        # 받은 좋아요 수
        likes_query = (
            select(func.sum(self.model_class.like_count))
            .select_from(self.model_class)
            .where(self.model_class.author_id == author_id)
        )
        likes_result = await self.session.execute(likes_query)
        total_likes = likes_result.scalar_one() or 0

        return {
            "total_comments": total_comments,
            "total_replies": total_replies,
            "total_likes_received": total_likes,
            "average_likes_per_comment": total_likes / total_comments if total_comments > 0 else 0
        }

    async def get_hourly_comment_distribution(self) -> Dict[int, int]:
        """시간대별 댓글 분포를 조회합니다."""
        query = (
            select(
                func.extract("hour", self.model_class.created_at).label("hour"),
                func.count().label("count")
            )
            .group_by(func.extract("hour", self.model_class.created_at))
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()} 