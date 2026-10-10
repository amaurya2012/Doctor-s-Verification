"""Business logic for posts, likes, comments, follows."""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.enums import NotificationType
from app.models.follow import Follow
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.services.notification_service import notify


class SocialError(Exception):
    """Raised for social-layer failures the route layer maps to HTTP errors."""


def create_post(db: Session, *, author: User, content: str, image_url: Optional[str]) -> Post:
    post = Post(author_id=author.id, content=content, image_url=image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_post(db: Session, *, post: Post, data: dict) -> Post:
    for field, value in data.items():
        if value is not None:
            setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, *, post: Post) -> None:
    db.delete(post)
    db.commit()


def _attach_view_fields(db: Session, posts: list[Post], viewer: Optional[User]) -> list[dict]:
    """Batch-compute like/comment counts and liked_by_me (avoids N+1 queries)."""
    if not posts:
        return []

    post_ids = [p.id for p in posts]

    like_counts = dict(
        db.execute(
            select(Like.post_id, func.count(Like.id)).where(Like.post_id.in_(post_ids)).group_by(Like.post_id)
        ).all()
    )
    comment_counts = dict(
        db.execute(
            select(Comment.post_id, func.count(Comment.id))
            .where(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
        ).all()
    )
    liked_post_ids: set[int] = set()
    if viewer is not None:
        liked_post_ids = set(
            db.execute(
                select(Like.post_id).where(Like.post_id.in_(post_ids), Like.user_id == viewer.id)
            ).scalars()
        )

    return [
        {
            "id": post.id,
            "content": post.content,
            "image_url": post.image_url,
            "author": post.author,
            "created_at": post.created_at,
            "like_count": like_counts.get(post.id, 0),
            "comment_count": comment_counts.get(post.id, 0),
            "liked_by_me": post.id in liked_post_ids,
        }
        for post in posts
    ]


def get_feed(db: Session, *, viewer: Optional[User], limit: int = 20, offset: int = 0) -> list[dict]:
    stmt = select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)
    posts = list(db.scalars(stmt).all())
    return _attach_view_fields(db, posts, viewer)


def get_post_view(db: Session, *, post: Post, viewer: Optional[User]) -> dict:
    return _attach_view_fields(db, [post], viewer)[0]


def like_post(db: Session, *, user: User, post: Post) -> None:
    db.add(Like(user_id=user.id, post_id=post.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return  # already liked -- idempotent

    if post.author_id != user.id:
        notify(
            db,
            recipient_id=post.author_id,
            type=NotificationType.LIKE,
            message=f"{user.username} liked your post",
            actor_id=user.id,
            related_object_id=post.id,
            related_object_type="post",
        )


def unlike_post(db: Session, *, user: User, post: Post) -> None:
    like = db.query(Like).filter(Like.user_id == user.id, Like.post_id == post.id).first()
    if like is not None:
        db.delete(like)
        db.commit()


def add_comment(db: Session, *, author: User, post: Post, content: str) -> Comment:
    comment = Comment(post_id=post.id, author_id=author.id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    if post.author_id != author.id:
        notify(
            db,
            recipient_id=post.author_id,
            type=NotificationType.COMMENT,
            message=f"{author.username} commented on your post",
            actor_id=author.id,
            related_object_id=post.id,
            related_object_type="post",
        )
    return comment


def list_comments(db: Session, *, post: Post, limit: int = 50, offset: int = 0) -> list[Comment]:
    stmt = (
        select(Comment)
        .where(Comment.post_id == post.id)
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def follow_user(db: Session, *, follower: User, followee: User) -> None:
    if follower.id == followee.id:
        raise SocialError("Cannot follow yourself")

    db.add(Follow(follower_id=follower.id, followee_id=followee.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return  # already following -- idempotent

    notify(
        db,
        recipient_id=followee.id,
        type=NotificationType.FOLLOW,
        message=f"{follower.username} started following you",
        actor_id=follower.id,
        related_object_id=follower.id,
        related_object_type="user",
    )


def unfollow_user(db: Session, *, follower: User, followee: User) -> None:
    follow = (
        db.query(Follow)
        .filter(Follow.follower_id == follower.id, Follow.followee_id == followee.id)
        .first()
    )
    if follow is not None:
        db.delete(follow)
        db.commit()


def get_follow_status(db: Session, *, viewer: Optional[User], target: User) -> dict:
    follower_count = db.scalar(select(func.count(Follow.id)).where(Follow.followee_id == target.id))
    following_count = db.scalar(select(func.count(Follow.id)).where(Follow.follower_id == target.id))
    following = False
    if viewer is not None:
        following = (
            db.query(Follow)
            .filter(Follow.follower_id == viewer.id, Follow.followee_id == target.id)
            .first()
            is not None
        )
    return {
        "following": following,
        "follower_count": follower_count or 0,
        "following_count": following_count or 0,
    }
