from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_db
from src.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from src.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.repositories.user import SQLAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """새로운 사용자를 등록합니다."""
    user_repo = SQLAlchemyUserRepository(session)

    # 이메일 중복 확인
    if await user_repo.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 사용자명 중복 확인
    if await user_repo.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # 새로운 사용자 생성
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    user = await user_repo.create(user)

    # 액세스 토큰 생성
    token = create_access_token(
        subject=str(user.id),
        claims={"role": user.role.value},
    )

    return token


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """사용자 로그인을 처리합니다."""
    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_email(request.email)

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token = create_access_token(
        subject=str(user.id),
        claims={"role": user.role.value},
    )

    return token


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """사용자의 비밀번호를 변경합니다."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )

    user_repo = SQLAlchemyUserRepository(session)
    current_user.hashed_password = get_password_hash(request.new_password)
    await user_repo.update(current_user) 