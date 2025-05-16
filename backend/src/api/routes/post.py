from math import ceil
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.dependencies.auth import get_current_active_user, get_optional_user
from src.api.dependencies.database import get_db
from src.api.schemas.post import (
    PostCreate,
    PostListResponse,
    PostResponse,
    PostStats,
    PostUpdate,
)
from src.domain.entities.post import Post, PostStatus
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.repositories.post import SQLAlchemyPostRepository

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    request: PostCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostResponse:
    """새로운 블로그 포스트를 생성합니다."""
    post = Post(
        title=request.title,
        content=request.content,
        excerpt=request.excerpt,
        featured_image=request.featured_image,
        tags=request.tags,
        category_id=request.category_id,
        is_featured=request.is_featured,
        allow_comments=request.allow_comments,
        status=request.status,
        author_id=current_user.id,
    )

    post_repo = SQLAlchemyPostRepository(session)
    created_post = await post_repo.create(post)
    return PostResponse.model_validate(created_post)


@router.get("", response_model=PostListResponse)
async def list_posts(
    current_user: Annotated[Optional[User], Depends(get_optional_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[PostStatus] = None,
    category_id: Optional[UUID] = None,
    author_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> PostListResponse:
    """블로그 포스트 목록을 조회합니다."""
    post_repo = SQLAlchemyPostRepository(session)
    skip = (page - 1) * size

    # 비로그인 사용자는 공개된 포스트만 볼 수 있음
    if not current_user:
        status = PostStatus.PUBLISHED

    # 관리자가 아닌 경우, 자신의 포스트만 볼 수 있음
    if current_user and current_user.role != UserRole.ADMIN:
        if author_id and author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own posts",
            )
        author_id = current_user.id

    # 조건에 따른 포스트 조회
    if search:
        posts = await post_repo.search_by_title(search, skip=skip, limit=size)
    elif tag:
        posts = await post_repo.search_by_tag(tag, skip=skip, limit=size)
    elif status:
        posts = await post_repo.get_by_status(status, skip=skip, limit=size)
    elif category_id:
        posts = await post_repo.get_by_category_id(category_id, skip=skip, limit=size)
    elif author_id:
        posts = await post_repo.get_by_author_id(author_id, skip=skip, limit=size)
    else:
        posts = await post_repo.get_all(skip=skip, limit=size)

    # 전체 포스트 수 계산
    total = len(posts)  # 실제로는 count 쿼리를 사용해야 함
    pages = ceil(total / size)

    return PostListResponse(
        items=posts,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: Annotated[Optional[User], Depends(get_optional_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostResponse:
    """특정 블로그 포스트를 조회합니다."""
    post_repo = SQLAlchemyPostRepository(session)
    post = await post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # 비공개 포스트는 작성자와 관리자만 볼 수 있음
    if post.status != PostStatus.PUBLISHED:
        if not current_user or (
            current_user.id != post.author_id
            and current_user.role != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this post",
            )

    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    request: PostUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostResponse:
    """블로그 포스트를 수정합니다."""
    post_repo = SQLAlchemyPostRepository(session)
    post = await post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # 작성자와 관리자만 수정 가능
    if current_user.id != post.author_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this post",
        )

    # 포스트 업데이트
    post.title = request.title
    post.content = request.content
    post.excerpt = request.excerpt
    post.featured_image = request.featured_image
    post.tags = request.tags
    post.category_id = request.category_id
    post.is_featured = request.is_featured
    post.allow_comments = request.allow_comments
    if request.status is not None:
        post.status = request.status

    updated_post = await post_repo.update(post)
    return PostResponse.model_validate(updated_post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """블로그 포스트를 삭제합니다."""
    post_repo = SQLAlchemyPostRepository(session)
    post = await post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # 작성자와 관리자만 삭제 가능
    if current_user.id != post.author_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this post",
        )

    await post_repo.delete(post_id)


@router.get("/stats/overview", response_model=PostStats)
async def get_post_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostStats:
    """블로그 포스트 통계를 조회합니다."""
    post_repo = SQLAlchemyPostRepository(session)

    # 통계 데이터 수집
    posts_by_status = await post_repo.get_post_counts_by_status()
    posts_by_category = await post_repo.get_post_counts_by_category()
    popular_tags = await post_repo.get_popular_tags(limit=10)

    total_posts = sum(posts_by_status.values())
    total_views = sum(post.view_count for post in await post_repo.get_all())
    total_likes = sum(post.like_count for post in await post_repo.get_all())
    # TODO: 댓글 수는 댓글 리포지토리 구현 후 추가

    return PostStats(
        total_posts=total_posts,
        total_views=total_views,
        total_likes=total_likes,
        total_comments=0,  # TODO: 댓글 수 추가
        posts_by_status=posts_by_status,
        posts_by_category=posts_by_category,
        popular_tags=popular_tags,
    ) 