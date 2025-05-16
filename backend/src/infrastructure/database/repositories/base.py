from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.base import Entity
from src.domain.repositories.base import BaseRepository
from src.infrastructure.database.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
EntityType = TypeVar("EntityType", bound=Entity)


class SQLAlchemyRepository(BaseRepository[EntityType], Generic[ModelType, EntityType]):
    """SQLAlchemy를 사용하는 기본 리포지토리 구현체"""

    def __init__(
        self,
        session: AsyncSession,
        model_class: Type[ModelType],
        entity_class: Type[EntityType],
    ):
        self.session = session
        self.model_class = model_class
        self.entity_class = entity_class

    async def create(self, entity: EntityType) -> EntityType:
        db_obj = self.model_class(**entity.model_dump(exclude={"id", "created_at", "updated_at"}))
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.entity_class.model_validate(db_obj)

    async def get_by_id(self, id: UUID) -> Optional[EntityType]:
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity_class.model_validate(db_obj)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[EntityType]:
        query = select(self.model_class).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def update(self, entity: EntityType) -> EntityType:
        query = select(self.model_class).where(self.model_class.id == entity.id)
        result = await self.session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            raise ValueError(f"Entity with id {entity.id} not found")
        
        obj_data = entity.model_dump(exclude={"id", "created_at", "updated_at"})
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
        
        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.entity_class.model_validate(db_obj)

    async def delete(self, id: UUID) -> bool:
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False
        await self.session.delete(db_obj)
        return True 