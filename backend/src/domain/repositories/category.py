from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ..entities.category import Category
from .base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """카테고리 리포지토리 인터페이스"""

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """슬러그로 카테고리를 조회합니다."""
        pass

    async def get_root_categories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """최상위 카테고리를 조회합니다."""
        pass

    async def get_children(
        self, parent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """하위 카테고리를 조회합니다."""
        pass

    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """상위 카테고리 계층을 조회합니다."""
        pass

    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """하위 카테고리 계층을 조회합니다."""
        pass

    # 통계 관련 메서드 추가
    async def get_category_post_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 포스트 수를 조회합니다."""
        pass

    async def get_category_view_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 조회수를 조회합니다."""
        pass

    async def get_category_comment_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 댓글 수를 조회합니다."""
        pass

    async def get_most_active_categories(
        self, limit: int = 10
    ) -> List[Tuple[Category, Dict[str, int]]]:
        """가장 활발한 카테고리를 조회합니다.
        
        Returns:
            List[Tuple[Category, Dict[str, int]]]: [
                (category, {
                    "posts": int,
                    "views": int,
                    "comments": int,
                    "likes": int
                }),
                ...
            ]
        """
        pass

    async def get_category_depth_stats(self) -> Dict[int, int]:
        """카테고리 깊이별 통계를 조회합니다.
        
        Returns:
            Dict[int, int]: {
                depth: count,
                ...
            }
        """
        pass

    async def get_category_growth_stats(
        self, days: int = 30
    ) -> Dict[str, List[Tuple[str, int]]]:
        """카테고리의 성장 통계를 조회합니다.
        
        Returns:
            Dict[str, List[Tuple[str, int]]]: {
                "new_posts": [(date, count), ...],
                "new_comments": [(date, count), ...],
                "new_views": [(date, count), ...],
                "new_likes": [(date, count), ...]
            }
        """
        pass 