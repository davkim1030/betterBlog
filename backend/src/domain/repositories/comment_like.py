from uuid import UUID

from src.domain.entities.comment_like import CommentLike
from .base import Repository


class CommentLikeRepository(Repository[CommentLike]):
    """댓글 좋아요 리포지토리 인터페이스"""

    async def get_by_user_and_comment(
        self, user_id: UUID, comment_id: UUID
    ) -> CommentLike | None:
        """사용자와 댓글로 좋아요를 조회합니다."""
        raise NotImplementedError

    async def get_likes_count_by_comment(self, comment_id: UUID) -> int:
        """댓글의 좋아요 수를 조회합니다."""
        raise NotImplementedError

    async def delete_by_user_and_comment(
        self, user_id: UUID, comment_id: UUID
    ) -> None:
        """사용자와 댓글로 좋아요를 삭제합니다."""
        raise NotImplementedError 