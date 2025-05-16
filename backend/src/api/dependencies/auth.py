from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.security import verify_token
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories.user import SQLAlchemyUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """현재 인증된 사용자를 반환합니다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_id(UUID(user_id))
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_optional_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """현재 사용자를 반환하되, 인증되지 않은 경우 None을 반환합니다."""
    if not token:
        return None
    try:
        return await get_current_user(token, session)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """현재 활성화된 사용자를 반환합니다."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """현재 슈퍼유저를 반환합니다."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def check_permissions(*allowed_roles: UserRole):
    """특정 역할에 대한 권한을 확인합니다."""
    
    async def permission_checker(
        current_user: Annotated[User, Security(get_current_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user

    return permission_checker 