from enum import Enum
from typing import Optional

from pydantic import EmailStr, HttpUrl

from .base import Entity


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(Entity):
    email: EmailStr
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
