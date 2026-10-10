"""Follow/unfollow and notification endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.db.base import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.social import FollowStatus, NotificationPublic
from app.services import social_service

router = APIRouter(tags=["social"])


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _get_user_or_404(db, user_id)
    try:
        social_service.follow_user(db, follower=current_user, followee=target)
    except social_service.SocialError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _get_user_or_404(db, user_id)
    social_service.unfollow_user(db, follower=current_user, followee=target)


@router.get("/users/{user_id}/follow-status", response_model=FollowStatus)
def follow_status(
    user_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    target = _get_user_or_404(db, user_id)
    return social_service.get_follow_status(db, viewer=viewer, target=target)


@router.get("/notifications", response_model=list[NotificationPublic])
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.recipient_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
