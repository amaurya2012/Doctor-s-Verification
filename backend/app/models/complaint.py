"""Complaint: user-filed report against a user, post, or doctor profile."""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ComplaintStatus

if TYPE_CHECKING:
    from app.models.user import User


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    complainant_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    target_object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_object_id: Mapped[int] = mapped_column(nullable=False)

    reason: Mapped[str] = mapped_column(String(150), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus), default=ComplaintStatus.OPEN, nullable=False
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    handled_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    complainant: Mapped["User"] = relationship(
        back_populates="complaints_filed", foreign_keys=[complainant_id]
    )

    def __repr__(self) -> str:
        return f"<Complaint id={self.id} status={self.status}>"
