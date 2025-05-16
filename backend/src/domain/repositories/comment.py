from typing import Dict, List, Tuple
from uuid import UUID

from ..entities.comment import Comment
from .base import Repository


class CommentRepository(Repository[Comment]):
    """댓글 리포지토리 인터페이스"""

    async def get_by_post_id(
        self, post_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """게시물 ID로 댓글을 조회합니다."""
        pass

    async def get_by_author_id(
        self, author_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """작성자 ID로 댓글을 조회합니다."""
        pass

    async def get_replies(
        self, parent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """상위 댓글의 답글을 조회합니다."""
        pass

    async def get_root_comments(
        self, post_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """게시물의 최상위 댓글을 조회합니다."""
        pass

    # 통계 관련 메서드 추가
    async def get_comment_count_by_post(self, post_id: UUID) -> int:
        """게시물의 총 댓글 수를 조회합니다."""
        pass

    async def get_reply_count_by_comment(self, comment_id: UUID) -> int:
        """댓글의 답글 수를 조회합니다."""
        pass

    async def get_most_active_commenters(self, limit: int = 10) -> List[Tuple[UUID, int]]:
        """가장 활발한 댓글 작성자를 조회합니다."""
        pass

    async def get_most_commented_posts(self, limit: int = 10) -> List[Tuple[UUID, int]]:
        """댓글이 가장 많은 게시물을 조회합니다."""
        pass

    async def get_comment_stats_by_author(self, author_id: UUID) -> Dict[str, int]:
        """작성자의 댓글 통계를 조회합니다.
        
        Returns:
            Dict[str, int]: {
                "total_comments": int,
                "total_replies": int,
                "total_likes_received": int,
                "average_likes_per_comment": float
            }
        """
        pass

    async def get_hourly_comment_distribution(self) -> Dict[int, int]:
        """시간대별 댓글 분포를 조회합니다."""
        pass 