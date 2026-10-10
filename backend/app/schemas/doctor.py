"""Pydantic v2 schemas for the doctor discovery/verification module."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VerificationStatus
from app.schemas.user import UserPublic


class DoctorProfileCreate(BaseModel):
    specialization: str = Field(min_length=1, max_length=150)
    registration_number: str = Field(min_length=1, max_length=100)
    registration_council: str = Field(min_length=1, max_length=150)
    years_of_experience: int = Field(default=0, ge=0, le=80)
    clinic_name: Optional[str] = Field(default=None, max_length=200)
    clinic_address: Optional[str] = Field(default=None, max_length=400)
    consultation_fee: Optional[int] = Field(default=None, ge=0)


class DoctorProfileUpdate(BaseModel):
    specialization: Optional[str] = Field(default=None, max_length=150)
    years_of_experience: Optional[int] = Field(default=None, ge=0, le=80)
    clinic_name: Optional[str] = Field(default=None, max_length=200)
    clinic_address: Optional[str] = Field(default=None, max_length=400)
    consultation_fee: Optional[int] = Field(default=None, ge=0)


class CertificatePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_url: str


class DoctorProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    specialization: str
    registration_council: str
    years_of_experience: int
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    consultation_fee: Optional[int] = None
    verification_status: VerificationStatus
    user: UserPublic


class DoctorProfileMe(DoctorProfilePublic):
    registration_number: str
    verification_notes: Optional[str] = None
    certificates: list[CertificatePublic] = []


class DoctorVerifyDecision(BaseModel):
    approve: bool
    notes: Optional[str] = Field(default=None, max_length=1000)
