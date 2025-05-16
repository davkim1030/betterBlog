from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user import UserRepository
from src.infrastructure.database.models.user import User as UserModel
from .base import SQLAlchemyRepository


class SQLAlchemyUserRepository(SQLAlchemyRepository[UserModel, User], UserRepository):
    """SQLAlchemy를 사용하는 사용자 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity_class.model_validate(db_obj)

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(self.model_class).where(self.model_class.username == username)
        result = await self.session.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity_class.model_validate(db_obj) 