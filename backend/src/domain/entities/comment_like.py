from uuid import UUID

from .base import Entity

 
class CommentLike(Entity):
    """댓글 좋아요 엔티티"""
    user_id: UUID
    comment_id: UUID 