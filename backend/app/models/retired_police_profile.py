"""RetiredPoliceProfile: verified retired-police users who can respond to SOS incidents."""
from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.user import User


class RetiredPoliceProfile(Base):
    __tablename__ = "retired_police_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    service_id_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    rank: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(150), nullable=False)
    years_of_service: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retirement_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[date]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="retired_police_profile", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<RetiredPoliceProfile user_id={self.user_id} status={self.verification_status}>"
