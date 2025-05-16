from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.category import Category
from src.domain.repositories.category import CategoryRepository
from src.infrastructure.database.models.category import Category as CategoryModel
from src.infrastructure.database.repositories.base import SQLAlchemyRepository


class SQLAlchemyCategoryRepository(SQLAlchemyRepository[CategoryModel, Category], CategoryRepository):
    """SQLAlchemy를 사용하는 카테고리 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CategoryModel, Category)

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """슬러그로 카테고리를 조회합니다."""
        query = select(self.model_class).where(self.model_class.slug == slug)
        result = await self.session.execute(query)
        if obj := result.scalar_one_or_none():
            return self.entity_class.model_validate(obj)
        return None

    async def get_by_parent_id(self, parent_id: UUID) -> list[Category]:
        """부모 ID로 하위 카테고리를 조회합니다."""
        query = select(self.model_class).where(self.model_class.parent_id == parent_id)
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_root_categories(self) -> list[Category]:
        """최상위 카테고리를 조회합니다."""
        query = select(self.model_class).where(self.model_class.parent_id.is_(None))
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_children(
        self, parent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """하위 카테고리를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """상위 카테고리 계층을 조회합니다."""
        query = """
        WITH RECURSIVE ancestors AS (
            SELECT *
            FROM categories
            WHERE id = :category_id
            UNION ALL
            SELECT c.*
            FROM categories c
            JOIN ancestors a ON c.id = a.parent_id
        )
        SELECT * FROM ancestors WHERE id != :category_id
        """
        result = await self.session.execute(text(query), {"category_id": category_id})
        return [self.entity_class.model_validate(obj) for obj in result.all()]

    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """하위 카테고리 계층을 조회합니다."""
        query = """
        WITH RECURSIVE descendants AS (
            SELECT *
            FROM categories
            WHERE id = :category_id
            UNION ALL
            SELECT c.*
            FROM categories c
            JOIN descendants d ON c.parent_id = d.id
        )
        SELECT * FROM descendants WHERE id != :category_id
        """
        result = await self.session.execute(text(query), {"category_id": category_id})
        return [self.entity_class.model_validate(obj) for obj in result.all()]

    async def get_category_post_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 포스트 수를 조회합니다."""
        query = """
        SELECT c.id, COUNT(p.id) as post_count
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id
        GROUP BY c.id
        """
        result = await self.session.execute(text(query))
        return {row.id: row.post_count for row in result.all()}

    async def get_category_view_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 조회수를 조회합니다."""
        query = """
        SELECT c.id, COALESCE(SUM(p.view_count), 0) as view_count
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id
        GROUP BY c.id
        """
        result = await self.session.execute(text(query))
        return {row.id: row.view_count for row in result.all()}

    async def get_category_comment_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 댓글 수를 조회합니다."""
        query = """
        SELECT c.id, COUNT(cm.id) as comment_count
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id
        LEFT JOIN comments cm ON p.id = cm.post_id
        GROUP BY c.id
        """
        result = await self.session.execute(text(query))
        return {row.id: row.comment_count for row in result.all()}

    async def get_most_active_categories(
        self, limit: int = 10
    ) -> List[Tuple[Category, Dict[str, int]]]:
        """가장 활발한 카테고리를 조회합니다."""
        query = """
        SELECT 
            c.*,
            COUNT(DISTINCT p.id) as posts,
            COALESCE(SUM(p.view_count), 0) as views,
            COUNT(DISTINCT cm.id) as comments,
            COALESCE(SUM(p.like_count), 0) as likes
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id
        LEFT JOIN comments cm ON p.id = cm.post_id
        GROUP BY c.id
        ORDER BY posts DESC, views DESC
        LIMIT :limit
        """
        result = await self.session.execute(text(query), {"limit": limit})
        categories = []
        for row in result.all():
            category = self.entity_class.model_validate(row)
            stats = {
                "posts": row.posts,
                "views": row.views,
                "comments": row.comments,
                "likes": row.likes
            }
            categories.append((category, stats))
        return categories

    async def get_category_depth_stats(self) -> Dict[int, int]:
        """카테고리 깊이별 통계를 조회합니다."""
        query = """
        WITH RECURSIVE category_depths AS (
            SELECT id, 0 as depth
            FROM categories
            WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, cd.depth + 1
            FROM categories c
            JOIN category_depths cd ON c.parent_id = cd.id
        )
        SELECT depth, COUNT(*) as count
        FROM category_depths
        GROUP BY depth
        ORDER BY depth
        """
        result = await self.session.execute(text(query))
        return {row.depth: row.count for row in result.all()}

    async def get_category_growth_stats(
        self, days: int = 30
    ) -> Dict[str, List[Tuple[str, int]]]:
        """카테고리의 성장 통계를 조회합니다."""
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
            COUNT(DISTINCT CASE WHEN p.created_at::date = d.date THEN p.id END) as new_posts,
            COUNT(DISTINCT CASE WHEN cm.created_at::date = d.date THEN cm.id END) as new_comments,
            COALESCE(SUM(CASE WHEN p.created_at::date = d.date THEN p.view_count END), 0) as new_views,
            COALESCE(SUM(CASE WHEN p.created_at::date = d.date THEN p.like_count END), 0) as new_likes
        FROM dates d
        LEFT JOIN categories c ON true
        LEFT JOIN posts p ON c.id = p.category_id
        LEFT JOIN comments cm ON p.id = cm.post_id
        GROUP BY d.date
        ORDER BY d.date
        """
        result = await self.session.execute(text(query), {"days": days})
        stats = {
            "new_posts": [],
            "new_comments": [],
            "new_views": [],
            "new_likes": []
        }
        for row in result.all():
            stats["new_posts"].append((row.date, row.new_posts))
            stats["new_comments"].append((row.date, row.new_comments))
            stats["new_views"].append((row.date, row.new_views))
            stats["new_likes"].append((row.date, row.new_likes))
        return stats 