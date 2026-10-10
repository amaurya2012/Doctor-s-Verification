"""Pydantic v2 schemas for SOS incidents and complaints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SOSStatus, ComplaintStatus
from app.schemas.user import UserPublic


class SOSIncidentCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address_hint: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = Field(default=None, max_length=1000)


class SOSIncidentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latitude: float
    longitude: float
    address_hint: Optional[str] = None
    description: Optional[str] = None
    status: SOSStatus
    reporter: UserPublic
    responder: Optional[UserPublic] = None
    created_at: datetime


class SOSStatusUpdate(BaseModel):
    status: SOSStatus


VALID_COMPLAINT_TARGETS = {"user", "post", "doctor_profile"}


class ComplaintCreate(BaseModel):
    target_object_type: str = Field(min_length=1, max_length=50)
    target_object_id: int
    reason: str = Field(min_length=1, max_length=150)
    details: Optional[str] = Field(default=None, max_length=2000)


class ComplaintPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_object_type: str
    target_object_id: int
    reason: str
    details: Optional[str] = None
    status: ComplaintStatus
    resolution_notes: Optional[str] = None
    complainant: UserPublic
    created_at: datetime


class ComplaintResolve(BaseModel):
    status: ComplaintStatus
    resolution_notes: Optional[str] = Field(default=None, max_length=2000)
