from typing import Generic, TypeVar
from uuid import UUID

from src.domain.entities.base import Entity

T = TypeVar("T", bound=Entity)


class Repository(Generic[T]):
    """기본 리포지토리 인터페이스"""

    async def create(self, entity: T) -> T:
        """새로운 엔티티를 생성합니다."""
        raise NotImplementedError

    async def get_by_id(self, id: UUID) -> T | None:
        """ID로 엔티티를 조회합니다."""
        raise NotImplementedError

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """모든 엔티티를 조회합니다."""
        raise NotImplementedError

    async def update(self, entity: T) -> T:
        """엔티티를 수정합니다."""
        raise NotImplementedError

    async def delete(self, id: UUID) -> None:
        """엔티티를 삭제합니다."""
        raise NotImplementedError 