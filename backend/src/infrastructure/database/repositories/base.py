from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.base import Entity
from src.domain.repositories.base import Repository
from src.infrastructure.database.models.base import BaseModel

Model = TypeVar("Model", bound=BaseModel)
T = TypeVar("T", bound=Entity)


class SQLAlchemyRepository(Generic[Model, T], Repository[T]):
    """SQLAlchemy를 사용하는 기본 리포지토리 구현체"""

    def __init__(
        self,
        session: AsyncSession,
        model_class: Type[Model],
        entity_class: Type[T],
    ):
        self.session = session
        self.model_class = model_class
        self.entity_class = entity_class

    async def create(self, entity: T) -> T:
        """새로운 엔티티를 생성합니다."""
        db_obj = self.model_class(**entity.model_dump(exclude={"id"}))
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return self.entity_class.model_validate(db_obj)

    async def get_by_id(self, id: UUID) -> T | None:
        """ID로 엔티티를 조회합니다."""
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        if obj := result.scalar_one_or_none():
            return self.entity_class.model_validate(obj)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """모든 엔티티를 조회합니다."""
        query = select(self.model_class).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def update(self, entity: T) -> T:
        """엔티티를 수정합니다."""
        query = select(self.model_class).where(self.model_class.id == entity.id)
        result = await self.session.execute(query)
        if db_obj := result.scalar_one_or_none():
            # 엔티티의 데이터로 모델 객체를 업데이트
            for key, value in entity.model_dump(exclude={"id"}).items():
                setattr(db_obj, key, value)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return self.entity_class.model_validate(db_obj)
        return None

    async def delete(self, id: UUID) -> None:
        """엔티티를 삭제합니다."""
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        if db_obj := result.scalar_one_or_none():
            await self.session.delete(db_obj)
            await self.session.commit() 