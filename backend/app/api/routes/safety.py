"""Safety module endpoints: SOS incidents and complaints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.base import get_db
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus
from app.models.sos_incident import SOSIncident
from app.models.user import User
from app.schemas.safety import (
    SOSIncidentCreate,
    SOSIncidentPublic,
    SOSStatusUpdate,
    ComplaintCreate,
    ComplaintPublic,
    ComplaintResolve,
)
from app.services import safety_service
from app.services.safety_service import SafetyError

sos_router = APIRouter(prefix="/sos", tags=["safety"])
complaints_router = APIRouter(prefix="/complaints", tags=["safety"])


def _get_incident_or_404(db: Session, incident_id: int) -> SOSIncident:
    incident = db.get(SOSIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS incident not found")
    return incident


@sos_router.post("", response_model=SOSIncidentPublic, status_code=status.HTTP_201_CREATED)
def create_sos(
    payload: SOSIncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return safety_service.create_incident(
        db,
        reporter=current_user,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address_hint=payload.address_hint,
        description=payload.description,
    )


@sos_router.get("/mine", response_model=list[SOSIncidentPublic])
def my_incidents(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return safety_service.list_my_incidents(db, reporter=current_user, limit=limit, offset=offset)


@sos_router.get("/open", response_model=list[SOSIncidentPublic])
def open_incidents(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not safety_service.can_respond_to_sos(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified retired-police users or admins can view the open SOS queue",
        )
    return safety_service.list_open_incidents(db, limit=limit, offset=offset)


@sos_router.post("/{incident_id}/respond", response_model=SOSIncidentPublic)
def respond_to_sos(
    incident_id: int,
    payload: SOSStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not safety_service.can_respond_to_sos(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified retired-police users or admins can respond to SOS incidents",
        )
    incident = _get_incident_or_404(db, incident_id)
    return safety_service.respond_to_incident(
        db, incident=incident, responder=current_user, new_status=payload.status
    )


def _get_complaint_or_404(db: Session, complaint_id: int) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return complaint


@complaints_router.post("", response_model=ComplaintPublic, status_code=status.HTTP_201_CREATED)
def file_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return safety_service.create_complaint(
            db,
            complainant=current_user,
            target_object_type=payload.target_object_type,
            target_object_id=payload.target_object_id,
            reason=payload.reason,
            details=payload.details,
        )
    except SafetyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@complaints_router.get("/mine", response_model=list[ComplaintPublic])
def my_complaints(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return safety_service.list_my_complaints(db, complainant=current_user, limit=limit, offset=offset)


@complaints_router.get("/admin/all", response_model=list[ComplaintPublic])
def list_all_complaints(
    status_filter: ComplaintStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return safety_service.list_all_complaints(db, status_filter=status_filter, limit=limit, offset=offset)


@complaints_router.post("/admin/{complaint_id}/resolve", response_model=ComplaintPublic)
def resolve_complaint(
    complaint_id: int,
    payload: ComplaintResolve,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    return safety_service.resolve_complaint(
        db,
        complaint=complaint,
        admin=admin,
        new_status=payload.status,
        resolution_notes=payload.resolution_notes,
    )
