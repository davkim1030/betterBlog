from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ..entities.user import User, UserRole
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """사용자 리포지토리 인터페이스"""

    async def get_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        pass

    async def get_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자를 조회합니다."""
        pass

    # 통계 관련 메서드 추가
    async def get_user_counts_by_role(self) -> Dict[UserRole, int]:
        """역할별 사용자 수를 조회합니다."""
        pass

    async def get_most_active_users(self, limit: int = 10) -> List[Tuple[User, Dict[str, int]]]:
        """가장 활발한 사용자를 조회합니다.
        
        Returns:
            List[Tuple[User, Dict[str, int]]]: [
                (user, {
                    "posts": int,
                    "comments": int,
                    "likes_given": int,
                    "likes_received": int
                }),
                ...
            ]
        """
        pass

    async def get_new_users_count(self, days: int = 30) -> Dict[str, int]:
        """최근 N일간의 신규 사용자 수를 조회합니다."""
        pass

    async def get_user_engagement_stats(self, user_id: UUID) -> Dict[str, int]:
        """사용자의 참여도 통계를 조회합니다.
        
        Returns:
            Dict[str, int]: {
                "total_posts": int,
                "total_comments": int,
                "total_likes_given": int,
                "total_likes_received": int,
                "total_views_received": int,
                "days_since_join": int,
                "days_since_last_activity": int
            }
        """
        pass

    async def get_user_activity_timeline(
        self, user_id: UUID, days: int = 30
    ) -> Dict[str, List[Tuple[str, int]]]:
        """사용자의 활동 타임라인을 조회합니다.
        
        Returns:
            Dict[str, List[Tuple[str, int]]]: {
                "posts": [(date, count), ...],
                "comments": [(date, count), ...],
                "likes_given": [(date, count), ...],
                "likes_received": [(date, count), ...]
            }
        """
        pass 