from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.post import Post, PostStatus
from src.domain.repositories.post import PostRepository
from src.infrastructure.database.models.post import Post as PostModel
from .base import SQLAlchemyRepository


class SQLAlchemyPostRepository(SQLAlchemyRepository[PostModel, Post], PostRepository):
    """SQLAlchemy를 사용하는 블로그 포스트 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PostModel, Post)

    async def get_by_author_id(
        self, author_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
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
        query = (
            select(self.model_class)
            .where(self.model_class.status == status)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_featured(self, skip: int = 0, limit: int = 100) -> List[Post]:
        query = (
            select(self.model_class)
            .where(self.model_class.is_featured == True)  # noqa
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def search_by_title(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        query = (
            select(self.model_class)
            .where(self.model_class.title.ilike(f"%{query}%"))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def search_by_tag(
        self, tag: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        query = (
            select(self.model_class)
            .where(self.model_class.tags.contains([tag]))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()] 