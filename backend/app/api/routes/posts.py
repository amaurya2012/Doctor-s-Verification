"""Post/comment/like endpoints. Feed is public but personalizes liked_by_me when logged in."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.db.base import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas.social import PostCreate, PostUpdate, PostPublic, CommentCreate, CommentPublic
from app.services import social_service

router = APIRouter(prefix="/posts", tags=["posts"])


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("", response_model=PostPublic, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = social_service.create_post(
        db, author=current_user, content=payload.content, image_url=payload.image_url
    )
    return social_service.get_post_view(db, post=post, viewer=current_user)


@router.get("", response_model=list[PostPublic])
def get_feed(
    limit: int = 20,
    offset: int = 0,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return social_service.get_feed(db, viewer=viewer, limit=limit, offset=offset)


@router.get("/{post_id}", response_model=PostPublic)
def get_post(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    return social_service.get_post_view(db, post=post, viewer=viewer)


@router.patch("/{post_id}", response_model=PostPublic)
def update_post(
    post_id: int,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    updated = social_service.update_post(db, post=post, data=payload.model_dump(exclude_unset=True))
    return social_service.get_post_view(db, post=updated, viewer=current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post")
    social_service.delete_post(db, post=post)


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    social_service.like_post(db, user=current_user, post=_get_post_or_404(db, post_id))


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    social_service.unlike_post(db, user=current_user, post=_get_post_or_404(db, post_id))


@router.post("/{post_id}/comments", response_model=CommentPublic, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    return social_service.add_comment(db, author=current_user, post=post, content=payload.content)


@router.get("/{post_id}/comments", response_model=list[CommentPublic])
def list_comments(
    post_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    return social_service.list_comments(db, post=post, limit=limit, offset=offset)
