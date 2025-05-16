from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db as get_db_connection
 
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션을 제공하는 의존성 함수입니다."""
    async for session in get_db_connection():
        yield session 