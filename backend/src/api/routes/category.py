from math import ceil
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.dependencies.auth import get_current_active_user, get_optional_user
from src.api.dependencies.database import get_db
from src.api.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryStats,
    CategoryUpdate,
)
from src.domain.entities.category import Category
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.repositories.category import SQLAlchemyCategoryRepository

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """새로운 카테고리를 생성합니다. 관리자만 가능합니다."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create categories",
        )

    category_repo = SQLAlchemyCategoryRepository(session)

    # 슬러그 중복 검사
    if await category_repo.get_by_slug(request.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists",
        )

    # 부모 카테고리 존재 여부 확인
    if request.parent_id:
        parent = await category_repo.get_by_id(request.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    category = Category(
        name=request.name,
        slug=request.slug,
        description=request.description,
        parent_id=request.parent_id,
        order=request.order,
    )

    created_category = await category_repo.create(category)
    return CategoryResponse.model_validate(created_category)


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    parent_id: Optional[UUID] = None,
) -> CategoryListResponse:
    """카테고리 목록을 조회합니다."""
    category_repo = SQLAlchemyCategoryRepository(session)
    skip = (page - 1) * size

    # 부모 카테고리 ID가 주어진 경우 하위 카테고리만 조회
    if parent_id:
        categories = await category_repo.get_children(parent_id, skip=skip, limit=size)
    else:
        categories = await category_repo.get_root_categories(skip=skip, limit=size)

    # 각 카테고리의 포스트 수 조회
    post_counts = await category_repo.get_category_post_counts()
    for category in categories:
        setattr(category, "post_count", post_counts.get(category.id, 0))

    # 전체 카테고리 수 계산
    total = len(categories)  # 실제로는 count 쿼리를 사용해야 함
    pages = ceil(total / size)

    return CategoryListResponse(
        items=categories,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """특정 카테고리를 조회합니다."""
    category_repo = SQLAlchemyCategoryRepository(session)
    category = await category_repo.get_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # 포스트 수 조회
    post_counts = await category_repo.get_category_post_counts()
    setattr(category, "post_count", post_counts.get(category.id, 0))

    return CategoryResponse.model_validate(category)


@router.get("/{category_id}/ancestors", response_model=List[CategoryResponse])
async def get_category_ancestors(
    category_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> List[CategoryResponse]:
    """카테고리의 상위 계층을 조회합니다."""
    category_repo = SQLAlchemyCategoryRepository(session)
    
    # 카테고리 존재 여부 확인
    if not await category_repo.get_by_id(category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    ancestors = await category_repo.get_ancestors(category_id)
    
    # 포스트 수 조회
    post_counts = await category_repo.get_category_post_counts()
    for category in ancestors:
        setattr(category, "post_count", post_counts.get(category.id, 0))

    return [CategoryResponse.model_validate(category) for category in ancestors]


@router.get("/{category_id}/descendants", response_model=List[CategoryResponse])
async def get_category_descendants(
    category_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> List[CategoryResponse]:
    """카테고리의 하위 계층을 조회합니다."""
    category_repo = SQLAlchemyCategoryRepository(session)
    
    # 카테고리 존재 여부 확인
    if not await category_repo.get_by_id(category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    descendants = await category_repo.get_descendants(category_id)
    
    # 포스트 수 조회
    post_counts = await category_repo.get_category_post_counts()
    for category in descendants:
        setattr(category, "post_count", post_counts.get(category.id, 0))

    return [CategoryResponse.model_validate(category) for category in descendants]


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    request: CategoryUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """카테고리를 수정합니다. 관리자만 가능합니다."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update categories",
        )

    category_repo = SQLAlchemyCategoryRepository(session)
    category = await category_repo.get_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # 슬러그 중복 검사
    if request.slug and request.slug != category.slug:
        existing = await category_repo.get_by_slug(request.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this slug already exists",
            )

    # 부모 카테고리 존재 여부 확인
    if request.parent_id and request.parent_id != category.parent_id:
        parent = await category_repo.get_by_id(request.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
        # 자기 자신이나 자신의 하위 카테고리를 부모로 지정할 수 없음
        if request.parent_id == category_id or parent in await category_repo.get_descendants(category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set itself or its descendants as parent",
            )

    # 카테고리 업데이트
    if request.name is not None:
        category.name = request.name
    if request.slug is not None:
        category.slug = request.slug
    if request.description is not None:
        category.description = request.description
    if request.parent_id is not None:
        category.parent_id = request.parent_id
    if request.order is not None:
        category.order = request.order

    updated_category = await category_repo.update(category)
    
    # 포스트 수 조회
    post_counts = await category_repo.get_category_post_counts()
    setattr(updated_category, "post_count", post_counts.get(updated_category.id, 0))

    return CategoryResponse.model_validate(updated_category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """카테고리를 삭제합니다. 관리자만 가능합니다."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete categories",
        )

    category_repo = SQLAlchemyCategoryRepository(session)
    category = await category_repo.get_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # 하위 카테고리가 있는 경우 삭제 불가
    children = await category_repo.get_children(category_id)
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories",
        )

    await category_repo.delete(category_id)


@router.get("/stats/overview", response_model=CategoryStats)
async def get_category_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryStats:
    """카테고리 통계를 조회합니다."""
    category_repo = SQLAlchemyCategoryRepository(session)

    # 통계 데이터 수집
    categories = await category_repo.get_all()
    total_categories = len(categories)
    
    post_counts = await category_repo.get_category_post_counts()
    total_posts = sum(post_counts.values())
    
    view_counts = await category_repo.get_category_view_counts()
    total_views = sum(view_counts.values())
    
    depth_stats = await category_repo.get_category_depth_stats()
    most_active = await category_repo.get_most_active_categories(limit=10)

    return CategoryStats(
        total_categories=total_categories,
        total_posts=total_posts,
        total_views=total_views,
        categories_by_depth=depth_stats,
        most_active_categories=most_active,
    ) 