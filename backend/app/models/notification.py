"""Notification: a user-facing event (follow, like, comment, approval, SOS update...)."""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import NotificationType

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    related_object_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    related_object_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recipient: Mapped["User"] = relationship(back_populates="notifications", foreign_keys=[recipient_id])
    actor: Mapped[Optional["User"]] = relationship(foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.type} recipient_id={self.recipient_id}>"
