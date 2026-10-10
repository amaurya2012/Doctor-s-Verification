"""Shared helper for creating notifications."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.enums import NotificationType


def notify(
    db: Session,
    *,
    recipient_id: int,
    type: NotificationType,
    message: str,
    actor_id: Optional[int] = None,
    related_object_id: Optional[int] = None,
    related_object_type: Optional[str] = None,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        type=type,
        message=message,
        related_object_id=related_object_id,
        related_object_type=related_object_type,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
