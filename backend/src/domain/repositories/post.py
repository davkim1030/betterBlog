from typing import Dict, List, Tuple
from uuid import UUID

from ..entities.post import Post, PostStatus
from .base import Repository


class PostRepository(Repository[Post]):
    """블로그 포스트 리포지토리 인터페이스"""

    async def get_by_author_id(
        self, author_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """작성자 ID로 포스트를 조회합니다."""
        pass

    async def get_by_category_id(
        self, category_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """카테고리 ID로 포스트를 조회합니다."""
        pass

    async def get_by_status(
        self, status: PostStatus, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """상태로 포스트를 조회합니다."""
        pass

    async def get_featured(self, skip: int = 0, limit: int = 100) -> List[Post]:
        """주요 포스트를 조회합니다."""
        pass

    async def search_by_title(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """제목으로 포스트를 검색합니다."""
        pass

    async def search_by_tag(
        self, tag: str, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """태그로 포스트를 검색합니다."""
        pass

    # 통계 관련 메서드 추가
    async def get_post_counts_by_status(self) -> Dict[PostStatus, int]:
        """상태별 포스트 수를 조회합니다."""
        pass

    async def get_most_viewed_posts(self, limit: int = 10) -> List[Post]:
        """조회수가 가장 높은 포스트를 조회합니다."""
        pass

    async def get_most_liked_posts(self, limit: int = 10) -> List[Post]:
        """좋아요가 가장 많은 포스트를 조회합니다."""
        pass

    async def get_most_commented_posts(self, limit: int = 10) -> List[Tuple[Post, int]]:
        """댓글이 가장 많은 포스트를 조회합니다."""
        pass

    async def get_post_counts_by_category(self) -> Dict[UUID, int]:
        """카테고리별 포스트 수를 조회합니다."""
        pass

    async def get_popular_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """가장 많이 사용된 태그를 조회합니다."""
        pass

    async def get_author_stats(self, author_id: UUID) -> Dict[str, int]:
        """작성자의 포스트 통계를 조회합니다.
        
        Returns:
            Dict[str, int]: {
                "total_posts": int,
                "total_views": int,
                "total_likes": int,
                "total_comments": int,
                "drafts": int,
                "published": int,
                "archived": int
            }
        """
        pass 