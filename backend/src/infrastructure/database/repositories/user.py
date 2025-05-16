from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User, UserRole
from src.domain.repositories.user import UserRepository
from src.infrastructure.database.models.user import User as UserModel
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class SQLAlchemyUserRepository(SQLAlchemyRepository[UserModel, User], UserRepository):
    """SQLAlchemy를 사용하는 사용자 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        query = select(self.model_class).where(self.model_class.email == email)
        result = await self.session.execute(query)
        if obj := result.scalar_one_or_none():
            return self.entity_class.model_validate(obj)
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자를 조회합니다."""
        query = select(self.model_class).where(self.model_class.username == username)
        result = await self.session.execute(query)
        if obj := result.scalar_one_or_none():
            return self.entity_class.model_validate(obj)
        return None

    async def get_user_counts_by_role(self) -> Dict[UserRole, int]:
        """역할별 사용자 수를 조회합니다."""
        query = """
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
        """
        result = await self.session.execute(text(query))
        return {UserRole(row.role): row.count for row in result.all()}

    async def get_most_active_users(self, limit: int = 10) -> List[Tuple[User, Dict[str, int]]]:
        """가장 활발한 사용자를 조회합니다."""
        query = """
        SELECT 
            u.*,
            COUNT(DISTINCT p.id) as posts,
            COUNT(DISTINCT c.id) as comments,
            COALESCE(SUM(c.like_count), 0) as likes_given,
            COALESCE(SUM(p.like_count), 0) as likes_received
        FROM users u
        LEFT JOIN posts p ON u.id = p.author_id
        LEFT JOIN comments c ON u.id = c.author_id
        GROUP BY u.id
        ORDER BY posts DESC, comments DESC
        LIMIT :limit
        """
        result = await self.session.execute(text(query), {"limit": limit})
        users = []
        for row in result.all():
            user = self.entity_class.model_validate(row)
            stats = {
                "posts": row.posts,
                "comments": row.comments,
                "likes_given": row.likes_given,
                "likes_received": row.likes_received
            }
            users.append((user, stats))
        return users

    async def get_new_users_count(self, days: int = 30) -> Dict[str, int]:
        """최근 N일간의 신규 사용자 수를 조회합니다."""
        query = """
        WITH dates AS (
            SELECT generate_series(
                date_trunc('day', now()) - interval ':days days',
                date_trunc('day', now()),
                interval '1 day'
            )::date as date
        )
        SELECT 
            d.date::text,
            COUNT(DISTINCT CASE WHEN u.created_at::date = d.date THEN u.id END) as new_users
        FROM dates d
        LEFT JOIN users u ON u.created_at::date = d.date
        GROUP BY d.date
        ORDER BY d.date
        """
        result = await self.session.execute(text(query), {"days": days})
        return {row.date: row.new_users for row in result.all()}

    async def get_user_engagement_stats(self, user_id: UUID) -> Dict[str, int]:
        """사용자의 참여도 통계를 조회합니다."""
        query = """
        SELECT 
            COUNT(DISTINCT p.id) as total_posts,
            COUNT(DISTINCT c.id) as total_comments,
            COALESCE(SUM(c.like_count), 0) as total_likes_given,
            COALESCE(SUM(p.like_count), 0) as total_likes_received,
            COALESCE(SUM(p.view_count), 0) as total_views_received,
            EXTRACT(DAY FROM now() - u.created_at)::integer as days_since_join,
            EXTRACT(DAY FROM now() - GREATEST(
                COALESCE(MAX(p.updated_at), '1970-01-01'),
                COALESCE(MAX(c.updated_at), '1970-01-01'),
                u.created_at
            ))::integer as days_since_last_activity
        FROM users u
        LEFT JOIN posts p ON u.id = p.author_id
        LEFT JOIN comments c ON u.id = c.author_id
        WHERE u.id = :user_id
        GROUP BY u.id, u.created_at
        """
        result = await self.session.execute(text(query), {"user_id": user_id})
        if row := result.first():
            return {
                "total_posts": row.total_posts,
                "total_comments": row.total_comments,
                "total_likes_given": row.total_likes_given,
                "total_likes_received": row.total_likes_received,
                "total_views_received": row.total_views_received,
                "days_since_join": row.days_since_join,
                "days_since_last_activity": row.days_since_last_activity
            }
        return {
            "total_posts": 0,
            "total_comments": 0,
            "total_likes_given": 0,
            "total_likes_received": 0,
            "total_views_received": 0,
            "days_since_join": 0,
            "days_since_last_activity": 0
        }

    async def get_user_activity_timeline(
        self, user_id: UUID, days: int = 30
    ) -> Dict[str, List[Tuple[str, int]]]:
        """사용자의 활동 타임라인을 조회합니다."""
        query = """
        WITH dates AS (
            SELECT generate_series(
                date_trunc('day', now()) - interval ':days days',
                date_trunc('day', now()),
                interval '1 day'
            )::date as date
        )
        SELECT 
            d.date::text,
            COUNT(DISTINCT CASE WHEN p.created_at::date = d.date THEN p.id END) as posts,
            COUNT(DISTINCT CASE WHEN c.created_at::date = d.date THEN c.id END) as comments,
            COALESCE(SUM(CASE WHEN c.created_at::date = d.date THEN c.like_count END), 0) as likes_given,
            COALESCE(SUM(CASE WHEN p.created_at::date = d.date THEN p.like_count END), 0) as likes_received
        FROM dates d
        LEFT JOIN users u ON true
        LEFT JOIN posts p ON u.id = p.author_id AND p.created_at::date = d.date
        LEFT JOIN comments c ON u.id = c.author_id AND c.created_at::date = d.date
        WHERE u.id = :user_id
        GROUP BY d.date
        ORDER BY d.date
        """
        result = await self.session.execute(text(query), {"user_id": user_id, "days": days})
        stats = {
            "posts": [],
            "comments": [],
            "likes_given": [],
            "likes_received": []
        }
        for row in result.all():
            stats["posts"].append((row.date, row.posts))
            stats["comments"].append((row.date, row.comments))
            stats["likes_given"].append((row.date, row.likes_given))
            stats["likes_received"].append((row.date, row.likes_received))
        return stats 