"""Pydantic v2 schemas for User read/update."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole


class UserMe(UserPublic):
    email: str
    is_email_verified: bool
    is_admin: bool


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    bio: Optional[str] = Field(default=None, max_length=300)
    avatar_url: Optional[str] = None
