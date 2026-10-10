"""Doctor discovery/verification endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.base import get_db
from app.models.doctor_profile import DoctorProfile
from app.models.user import User
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfilePublic,
    DoctorProfileMe,
    CertificatePublic,
    DoctorVerifyDecision,
)
from app.services import doctor_service
from app.services.doctor_service import DoctorProfileError

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _get_own_profile_or_404(user: User) -> DoctorProfile:
    if user.doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No doctor profile for this user")
    return user.doctor_profile


def _get_profile_or_404(db: Session, profile_id: int) -> DoctorProfile:
    profile = db.get(DoctorProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return profile


@router.post("/profile", response_model=DoctorProfileMe, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: DoctorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return doctor_service.create_profile(db, user=current_user, data=payload.model_dump())
    except DoctorProfileError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/profile/me", response_model=DoctorProfileMe)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return _get_own_profile_or_404(current_user)


@router.patch("/profile/me", response_model=DoctorProfileMe)
def update_my_profile(
    payload: DoctorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile_or_404(current_user)
    return doctor_service.update_profile(db, profile=profile, data=payload.model_dump(exclude_unset=True))


@router.post("/profile/certificates", response_model=CertificatePublic, status_code=status.HTTP_201_CREATED)
def upload_certificate(
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile_or_404(current_user)
    try:
        return doctor_service.add_certificate(db, profile=profile, title=title, file=file.file)
    except DoctorProfileError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("", response_model=list[DoctorProfilePublic])
def search_doctors(
    specialization: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return doctor_service.search_doctors(
        db, specialization=specialization, verified_only=True, limit=limit, offset=offset
    )


@router.get("/{profile_id}", response_model=DoctorProfilePublic)
def get_doctor(profile_id: int, db: Session = Depends(get_db)):
    return _get_profile_or_404(db, profile_id)


# --- Admin routes ---------------------------------------------------------


@router.get("/admin/pending", response_model=list[DoctorProfileMe])
def list_pending_profiles(
    limit: int = 50,
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return doctor_service.list_pending(db, limit=limit, offset=offset)


@router.post("/admin/{profile_id}/verify", response_model=DoctorProfileMe)
def verify_profile(
    profile_id: int,
    payload: DoctorVerifyDecision,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(db, profile_id)
    return doctor_service.decide_verification(
        db, profile=profile, admin=admin, approve=payload.approve, notes=payload.notes
    )
