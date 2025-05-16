from typing import Dict, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.post import Post, PostStatus
from src.domain.repositories.post import PostRepository
from src.infrastructure.database.models.post import Post as PostModel
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class SQLAlchemyPostRepository(SQLAlchemyRepository[PostModel, Post], PostRepository):
    """SQLAlchemy를 사용하는 포스트 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PostModel, Post)

    async def get_by_author_id(
        self, author_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """작성자 ID로 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.author_id == author_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_category_id(
        self, category_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """카테고리 ID로 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.category_id == category_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_status(
        self, status: PostStatus, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """상태로 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.status == status)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_featured(self, skip: int = 0, limit: int = 100) -> List[Post]:
        """주요 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.is_featured == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def search_by_title(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """제목으로 포스트를 검색합니다."""
        search_query = (
            select(self.model_class)
            .where(self.model_class.title.ilike(f"%{query}%"))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(search_query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def search_by_tag(
        self, tag: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """태그로 포스트를 검색합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.tags.contains([tag]))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_post_counts_by_status(self) -> Dict[PostStatus, int]:
        """상태별 포스트 수를 조회합니다."""
        query = (
            select(self.model_class.status, func.count(self.model_class.id))
            .group_by(self.model_class.status)
        )
        result = await self.session.execute(query)
        return {status: count for status, count in result.all()}

    async def get_most_viewed_posts(self, limit: int = 10) -> List[Post]:
        """조회수가 가장 높은 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .order_by(self.model_class.view_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_most_liked_posts(self, limit: int = 10) -> List[Post]:
        """좋아요가 가장 많은 포스트를 조회합니다."""
        query = (
            select(self.model_class)
            .order_by(self.model_class.like_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_post_counts_by_category(self) -> Dict[UUID, int]:
        """카테고리별 포스트 수를 조회합니다."""
        query = (
            select(self.model_class.category_id, func.count(self.model_class.id))
            .group_by(self.model_class.category_id)
        )
        result = await self.session.execute(query)
        return {category_id: count for category_id, count in result.all()}

    async def get_popular_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """가장 많이 사용된 태그를 조회합니다."""
        # PostgreSQL의 unnest 함수를 사용하여 태그 배열을 펼침
        query = """
        SELECT tag, COUNT(*) as count
        FROM posts, unnest(tags) as tag
        GROUP BY tag
        ORDER BY count DESC
        LIMIT :limit
        """
        result = await self.session.execute(query, {"limit": limit})
        return [(tag, count) for tag, count in result.all()]

    async def get_author_stats(self, author_id: UUID) -> Dict[str, int]:
        """작성자의 포스트 통계를 조회합니다."""
        query = """
        SELECT 
            COUNT(*) as total_posts,
            SUM(view_count) as total_views,
            SUM(like_count) as total_likes,
            SUM(comment_count) as total_comments,
            COUNT(*) FILTER (WHERE status = 'draft') as drafts,
            COUNT(*) FILTER (WHERE status = 'published') as published,
            COUNT(*) FILTER (WHERE status = 'archived') as archived
        FROM posts
        WHERE author_id = :author_id
        """
        result = await self.session.execute(query, {"author_id": author_id})
        stats = result.first()
        return {
            "total_posts": stats.total_posts or 0,
            "total_views": stats.total_views or 0,
            "total_likes": stats.total_likes or 0,
            "total_comments": stats.total_comments or 0,
            "drafts": stats.drafts or 0,
            "published": stats.published or 0,
            "archived": stats.archived or 0,
        } 