from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.domain.entities.category import Category
from src.domain.repositories.category import CategoryRepository
from src.infrastructure.database.models.category import Category as CategoryModel
from src.infrastructure.database.models.post import Post as PostModel
from .base import SQLAlchemyRepository


class SQLAlchemyCategoryRepository(SQLAlchemyRepository[CategoryModel, Category], CategoryRepository):
    """SQLAlchemy를 사용하는 카테고리 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CategoryModel, Category)

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """슬러그로 카테고리를 조회합니다."""
        query = select(self.model_class).where(self.model_class.slug == slug)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self.entity_class.model_validate(model) if model else None

    async def get_root_categories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """최상위 카테고리를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.parent_id.is_(None))
            .order_by(self.model_class.order)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_children(
        self, parent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """하위 카테고리를 조회합니다."""
        query = (
            select(self.model_class)
            .where(self.model_class.parent_id == parent_id)
            .order_by(self.model_class.order)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [self.entity_class.model_validate(obj) for obj in result.scalars().all()]

    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """상위 카테고리 계층을 조회합니다."""
        ancestors = []
        current = await self.get_by_id(category_id)
        
        while current and current.parent_id:
            parent = await self.get_by_id(current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
                
        return ancestors

    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """하위 카테고리 계층을 조회합니다."""
        descendants = []
        children = await self.get_children(category_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(await self.get_descendants(child.id))
            
        return descendants

    async def get_category_post_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 포스트 수를 조회합니다."""
        query = (
            select(
                self.model_class.id,
                func.count(PostModel.id).label("post_count")
            )
            .outerjoin(PostModel, self.model_class.id == PostModel.category_id)
            .group_by(self.model_class.id)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def get_category_view_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 조회수를 조회합니다."""
        query = (
            select(
                self.model_class.id,
                func.sum(PostModel.view_count).label("view_count")
            )
            .outerjoin(PostModel, self.model_class.id == PostModel.category_id)
            .group_by(self.model_class.id)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] or 0 for row in result.all()}

    async def get_category_comment_counts(self) -> Dict[UUID, int]:
        """각 카테고리별 총 댓글 수를 조회합니다."""
        # TODO: 댓글 모델 구현 후 추가
        return {}

    async def get_most_active_categories(
        self, limit: int = 10
    ) -> List[Tuple[Category, Dict[str, int]]]:
        """가장 활발한 카테고리를 조회합니다."""
        query = (
            select(
                self.model_class,
                func.count(PostModel.id).label("posts"),
                func.sum(PostModel.view_count).label("views"),
                func.sum(PostModel.like_count).label("likes")
            )
            .outerjoin(PostModel, self.model_class.id == PostModel.category_id)
            .group_by(self.model_class.id)
            .order_by(func.count(PostModel.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        
        active_categories = []
        for row in result.all():
            category = self.entity_class.model_validate(row[0])
            stats = {
                "posts": row[1],
                "views": row[2] or 0,
                "likes": row[3] or 0,
                "comments": 0  # TODO: 댓글 수 추가
            }
            active_categories.append((category, stats))
            
        return active_categories

    async def get_category_depth_stats(self) -> Dict[int, int]:
        """카테고리 깊이별 통계를 조회합니다."""
        def calculate_depth(category: CategoryModel, cache: Dict[UUID, int]) -> int:
            if category.id in cache:
                return cache[category.id]
            
            if not category.parent_id:
                cache[category.id] = 0
                return 0
                
            parent_depth = calculate_depth(category.parent, cache)
            cache[category.id] = parent_depth + 1
            return cache[category.id]

        query = select(self.model_class)
        result = await self.session.execute(query)
        categories = result.scalars().all()
        
        depth_cache: Dict[UUID, int] = {}
        for category in categories:
            calculate_depth(category, depth_cache)
            
        depth_stats: Dict[int, int] = {}
        for depth in depth_cache.values():
            depth_stats[depth] = depth_stats.get(depth, 0) + 1
            
        return depth_stats 