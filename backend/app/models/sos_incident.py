"""SOSIncident: an emergency alert with location, handled by verified responders/admins."""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SOSStatus

if TYPE_CHECKING:
    from app.models.user import User


class SOSIncident(Base):
    __tablename__ = "sos_incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    responder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address_hint: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[SOSStatus] = mapped_column(SAEnum(SOSStatus), default=SOSStatus.OPEN, nullable=False)

    reporter: Mapped["User"] = relationship(back_populates="sos_incidents", foreign_keys=[reporter_id])
    responder: Mapped[Optional["User"]] = relationship(foreign_keys=[responder_id])

    def __repr__(self) -> str:
        return f"<SOSIncident id={self.id} status={self.status}>"
