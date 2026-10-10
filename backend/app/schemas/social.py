"""Pydantic v2 schemas for posts, comments, follows, notifications."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import NotificationType
from app.schemas.user import UserPublic


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    image_url: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    image_url: Optional[str] = None


class PostPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    image_url: Optional[str] = None
    author: UserPublic
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author: UserPublic
    created_at: datetime


class FollowStatus(BaseModel):
    following: bool
    follower_count: int
    following_count: int


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    message: str
    is_read: bool
    created_at: datetime
    actor: Optional[UserPublic] = None
