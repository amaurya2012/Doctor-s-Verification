"""Business logic for SOS incidents and complaints."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, NotificationType, SOSStatus
from app.models.sos_incident import SOSIncident
from app.models.user import User
from app.schemas.safety import VALID_COMPLAINT_TARGETS
from app.services.notification_service import notify


class SafetyError(Exception):
    """Raised for safety-module failures the route layer maps to HTTP errors."""


def create_incident(
    db: Session,
    *,
    reporter: User,
    latitude: float,
    longitude: float,
    address_hint: Optional[str],
    description: Optional[str],
) -> SOSIncident:
    incident = SOSIncident(
        reporter_id=reporter.id,
        latitude=latitude,
        longitude=longitude,
        address_hint=address_hint,
        description=description,
        status=SOSStatus.OPEN,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def list_open_incidents(db: Session, *, limit: int = 50, offset: int = 0) -> list[SOSIncident]:
    stmt = (
        select(SOSIncident)
        .where(SOSIncident.status.in_([SOSStatus.OPEN, SOSStatus.ACKNOWLEDGED]))
        .order_by(SOSIncident.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def list_my_incidents(db: Session, *, reporter: User, limit: int = 50, offset: int = 0) -> list[SOSIncident]:
    stmt = (
        select(SOSIncident)
        .where(SOSIncident.reporter_id == reporter.id)
        .order_by(SOSIncident.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def can_respond_to_sos(user: User) -> bool:
    """Verified retired-police users or admins can respond to SOS incidents."""
    if user.is_admin:
        return True
    profile = user.retired_police_profile
    return profile is not None and profile.verification_status.value == "approved"


def respond_to_incident(db: Session, *, incident: SOSIncident, responder: User, new_status: SOSStatus) -> SOSIncident:
    incident.status = new_status
    if new_status == SOSStatus.ACKNOWLEDGED and incident.responder_id is None:
        incident.responder_id = responder.id
    db.commit()
    db.refresh(incident)

    notify(
        db,
        recipient_id=incident.reporter_id,
        type=NotificationType.SOS_ALERT,
        message=f"Your SOS alert status changed to: {new_status.value}",
        actor_id=responder.id,
        related_object_id=incident.id,
        related_object_type="sos_incident",
    )
    return incident


def create_complaint(
    db: Session,
    *,
    complainant: User,
    target_object_type: str,
    target_object_id: int,
    reason: str,
    details: Optional[str],
) -> Complaint:
    if target_object_type not in VALID_COMPLAINT_TARGETS:
        raise SafetyError(f"Invalid target_object_type; must be one of {sorted(VALID_COMPLAINT_TARGETS)}")

    complaint = Complaint(
        complainant_id=complainant.id,
        target_object_type=target_object_type,
        target_object_id=target_object_id,
        reason=reason,
        details=details,
        status=ComplaintStatus.OPEN,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def list_my_complaints(db: Session, *, complainant: User, limit: int = 50, offset: int = 0) -> list[Complaint]:
    stmt = (
        select(Complaint)
        .where(Complaint.complainant_id == complainant.id)
        .order_by(Complaint.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def list_all_complaints(
    db: Session, *, status_filter: Optional[ComplaintStatus] = None, limit: int = 50, offset: int = 0
) -> list[Complaint]:
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if status_filter is not None:
        stmt = stmt.where(Complaint.status == status_filter)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def resolve_complaint(
    db: Session, *, complaint: Complaint, admin: User, new_status: ComplaintStatus, resolution_notes: Optional[str]
) -> Complaint:
    complaint.status = new_status
    complaint.resolution_notes = resolution_notes
    complaint.handled_by_admin_id = admin.id
    db.commit()
    db.refresh(complaint)

    notify(
        db,
        recipient_id=complaint.complainant_id,
        type=NotificationType.COMPLAINT_UPDATE,
        message=f"Your complaint status changed to: {new_status.value}",
        actor_id=admin.id,
        related_object_id=complaint.id,
        related_object_type="complaint",
    )
    return complaint
