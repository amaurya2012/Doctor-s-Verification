"""DoctorProfile: genuinely one-to-one with User via UNIQUE user_id."""
from datetime import date
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.certificate import Certificate


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    registration_council: Mapped[str] = mapped_column(String(150), nullable=False)
    years_of_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clinic_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    clinic_address: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    consultation_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[date]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="doctor_profile", foreign_keys=[user_id])
    certificates: Mapped[List["Certificate"]] = relationship(
        back_populates="doctor_profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DoctorProfile user_id={self.user_id} status={self.verification_status}>"
