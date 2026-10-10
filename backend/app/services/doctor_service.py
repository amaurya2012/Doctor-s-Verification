"""Business logic for doctor profiles, certificates, and the admin verification workflow."""
from datetime import timezone, datetime
from typing import BinaryIO, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cloudinary_client import upload_file
from app.models.certificate import Certificate
from app.models.doctor_profile import DoctorProfile
from app.models.enums import UserRole, VerificationStatus, NotificationType
from app.models.user import User
from app.services.notification_service import notify


class DoctorProfileError(Exception):
    """Raised for doctor-profile failures the route layer maps to HTTP errors."""


def create_profile(db: Session, *, user: User, data: dict) -> DoctorProfile:
    if user.doctor_profile is not None:
        raise DoctorProfileError("Doctor profile already exists for this user")

    profile = DoctorProfile(user_id=user.id, **data)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DoctorProfileError("A doctor profile already exists for this user or registration number")
    db.refresh(profile)

    if user.role == UserRole.PATIENT:
        user.role = UserRole.DOCTOR
        db.commit()

    return profile


def update_profile(db: Session, *, profile: DoctorProfile, data: dict) -> DoctorProfile:
    for field, value in data.items():
        if value is not None:
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def add_certificate(db: Session, *, profile: DoctorProfile, title: str, file: BinaryIO) -> Certificate:
    try:
        result = upload_file(file, folder=f"doctorverify/certificates/{profile.user_id}")
    except RuntimeError as e:
        raise DoctorProfileError(str(e))

    cert = Certificate(
        doctor_profile_id=profile.id,
        title=title,
        file_url=result.url,
        cloudinary_public_id=result.public_id,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


def search_doctors(
    db: Session,
    *,
    specialization: Optional[str] = None,
    verified_only: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> list[DoctorProfile]:
    stmt = select(DoctorProfile)
    if verified_only:
        stmt = stmt.where(DoctorProfile.verification_status == VerificationStatus.APPROVED)
    if specialization:
        stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def list_pending(db: Session, *, limit: int = 50, offset: int = 0) -> list[DoctorProfile]:
    stmt = (
        select(DoctorProfile)
        .where(DoctorProfile.verification_status == VerificationStatus.PENDING)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def decide_verification(
    db: Session, *, profile: DoctorProfile, admin: User, approve: bool, notes: Optional[str]
) -> DoctorProfile:
    profile.verification_status = VerificationStatus.APPROVED if approve else VerificationStatus.REJECTED
    profile.verification_notes = notes
    profile.verified_by_admin_id = admin.id
    profile.verified_at = datetime.now(timezone.utc).date()
    db.commit()
    db.refresh(profile)

    notify(
        db,
        recipient_id=profile.user_id,
        type=NotificationType.DOCTOR_APPROVED if approve else NotificationType.DOCTOR_REJECTED,
        message=(
            "Your doctor profile has been approved."
            if approve
            else f"Your doctor profile was rejected. Reason: {notes or 'not specified'}"
        ),
        actor_id=admin.id,
        related_object_id=profile.id,
        related_object_type="doctor_profile",
    )
    return profile
