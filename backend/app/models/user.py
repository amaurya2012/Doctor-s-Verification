"""User model: core identity + auth. Role-specific data lives in one-to-one profile tables."""
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, AuthProvider

if TYPE_CHECKING:
    from app.models.doctor_profile import DoctorProfile
    from app.models.retired_police_profile import RetiredPoliceProfile
    from app.models.post import Post
    from app.models.comment import Comment
    from app.models.notification import Notification
    from app.models.sos_incident import SOSIncident
    from app.models.complaint import Complaint


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(
        SAEnum(AuthProvider), default=AuthProvider.LOCAL, nullable=False
    )
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.PATIENT, nullable=False)

    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # True one-to-one: uselist=False on the ORM side AND a UNIQUE constraint
    # on the FK column (see DoctorProfile.user_id) enforce it at the DB level.
    doctor_profile: Mapped[Optional["DoctorProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="DoctorProfile.user_id",
    )
    retired_police_profile: Mapped[Optional["RetiredPoliceProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="RetiredPoliceProfile.user_id",
    )

    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="recipient",
        foreign_keys="Notification.recipient_id",
        cascade="all, delete-orphan",
    )

    sos_incidents: Mapped[List["SOSIncident"]] = relationship(
        back_populates="reporter",
        foreign_keys="SOSIncident.reporter_id",
        cascade="all, delete-orphan",
    )
    complaints_filed: Mapped[List["Complaint"]] = relationship(
        back_populates="complainant",
        foreign_keys="Complaint.complainant_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role}>"
