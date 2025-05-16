from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from ..entities.base import Entity

T = TypeVar("T", bound=Entity)


class BaseRepository(ABC, Generic[T]):
    """기본 리포지토리 인터페이스"""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """새로운 엔티티를 생성합니다."""
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """ID로 엔티티를 조회합니다."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """모든 엔티티를 조회합니다."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """엔티티를 업데이트합니다."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """엔티티를 삭제합니다."""
        pass 