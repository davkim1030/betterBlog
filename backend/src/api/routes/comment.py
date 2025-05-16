from math import ceil
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_db
from src.api.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentStats,
    CommentUpdate,
)
from src.domain.entities.comment import Comment
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.repositories.comment import SQLAlchemyCommentRepository
from src.infrastructure.database.repositories.post import SQLAlchemyPostRepository
from src.infrastructure.database.repositories.comment_like import SQLAlchemyCommentLikeRepository

router = APIRouter(tags=["comments"])


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: UUID,
    request: CommentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentResponse:
    """새로운 댓글을 생성합니다."""
    # 게시물 존재 여부 확인
    post_repo = SQLAlchemyPostRepository(session)
    post = await post_repo.get_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # 게시물에 댓글 작성이 허용되어 있는지 확인
    if not post.allow_comments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Comments are not allowed for this post",
        )

    comment_repo = SQLAlchemyCommentRepository(session)

    # 부모 댓글 존재 여부 확인
    if request.parent_id:
        parent = await comment_repo.get_by_id(request.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )
        if parent.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to different post",
            )

    comment = Comment(
        content=request.content,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=request.parent_id,
        is_edited=False,
        like_count=0,
    )

    created_comment = await comment_repo.create(comment)
    
    # 답글 수 설정
    reply_count = await comment_repo.get_reply_count_by_comment(created_comment.id)
    setattr(created_comment, "reply_count", reply_count)
    
    return CommentResponse.model_validate(created_comment)


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    parent_id: Optional[UUID] = None,
) -> CommentListResponse:
    """게시물의 댓글 목록을 조회합니다."""
    # 게시물 존재 여부 확인
    post_repo = SQLAlchemyPostRepository(session)
    if not await post_repo.get_by_id(post_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    comment_repo = SQLAlchemyCommentRepository(session)
    skip = (page - 1) * size

    # 부모 댓글 ID가 주어진 경우 답글만 조회
    if parent_id:
        comments = await comment_repo.get_replies(parent_id, skip=skip, limit=size)
    else:
        comments = await comment_repo.get_root_comments(post_id, skip=skip, limit=size)

    # 각 댓글의 답글 수 조회
    for comment in comments:
        reply_count = await comment_repo.get_reply_count_by_comment(comment.id)
        setattr(comment, "reply_count", reply_count)

    # 전체 댓글 수 계산
    total = len(comments)  # 실제로는 count 쿼리를 사용해야 함
    pages = ceil(total / size)

    return CommentListResponse(
        items=comments,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentResponse:
    """특정 댓글을 조회합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)
    comment = await comment_repo.get_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # 답글 수 조회
    reply_count = await comment_repo.get_reply_count_by_comment(comment.id)
    setattr(comment, "reply_count", reply_count)

    return CommentResponse.model_validate(comment)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    request: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentResponse:
    """댓글을 수정합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)
    comment = await comment_repo.get_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # 작성자와 관리자만 수정 가능
    if current_user.id != comment.author_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this comment",
        )

    # 댓글 업데이트
    comment.content = request.content
    comment.is_edited = True

    updated_comment = await comment_repo.update(comment)
    
    # 답글 수 조회
    reply_count = await comment_repo.get_reply_count_by_comment(updated_comment.id)
    setattr(updated_comment, "reply_count", reply_count)

    return CommentResponse.model_validate(updated_comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """댓글을 삭제합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)
    comment = await comment_repo.get_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # 작성자와 관리자만 삭제 가능
    if current_user.id != comment.author_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this comment",
        )

    await comment_repo.delete(comment_id)


@router.post("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_comment(
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """댓글에 좋아요를 추가합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)
    comment = await comment_repo.get_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # 좋아요 중복 확인
    like_repo = SQLAlchemyCommentLikeRepository(session)
    existing_like = await like_repo.get_by_user_and_comment(current_user.id, comment_id)
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already liked this comment",
        )

    # 좋아요 생성
    like = CommentLike(
        user_id=current_user.id,
        comment_id=comment_id,
    )
    await like_repo.create(like)

    # 댓글의 좋아요 수 증가
    comment.like_count += 1
    await comment_repo.update(comment)


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_comment(
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """댓글의 좋아요를 취소합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)
    comment = await comment_repo.get_by_id(comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # 좋아요 확인
    like_repo = SQLAlchemyCommentLikeRepository(session)
    if not await like_repo.delete_by_user_and_comment(current_user.id, comment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this comment",
        )

    # 댓글의 좋아요 수 감소
    if comment.like_count > 0:
        comment.like_count -= 1
        await comment_repo.update(comment)


@router.get("/comments/stats/overview", response_model=CommentStats)
async def get_comment_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentStats:
    """댓글 통계를 조회합니다."""
    comment_repo = SQLAlchemyCommentRepository(session)

    # 전체 댓글 수
    comments = await comment_repo.get_all()
    total_comments = len(comments)
    
    # 최상위 댓글과 답글 수
    total_root_comments = len([c for c in comments if not c.parent_id])
    total_replies = total_comments - total_root_comments
    
    # 전체 좋아요 수
    total_likes = sum(comment.like_count for comment in comments)
    
    # 시간대별 댓글 분포
    comments_by_hour = await comment_repo.get_hourly_comment_distribution()
    
    # 가장 활발한 댓글 작성자
    most_active_commenters = await comment_repo.get_most_active_commenters(limit=10)
    
    # 가장 많은 좋아요를 받은 댓글
    most_liked_comments = sorted(
        comments,
        key=lambda x: x.like_count,
        reverse=True
    )[:10]
    
    # 가장 많은 답글을 받은 댓글
    most_replied_comments = []
    for comment in comments:
        if not comment.parent_id:  # 최상위 댓글만 확인
            reply_count = await comment_repo.get_reply_count_by_comment(comment.id)
            if reply_count > 0:
                most_replied_comments.append((comment, reply_count))
    
    most_replied_comments.sort(key=lambda x: x[1], reverse=True)
    most_replied_comments = most_replied_comments[:10]

    return CommentStats(
        total_comments=total_comments,
        total_root_comments=total_root_comments,
        total_replies=total_replies,
        total_likes=total_likes,
        comments_by_hour=comments_by_hour,
        most_active_commenters=most_active_commenters,
        most_liked_comments=most_liked_comments,
        most_replied_comments=most_replied_comments,
    ) 