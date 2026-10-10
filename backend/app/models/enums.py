"""Shared enums for models."""
import enum


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    RETIRED_POLICE = "retired_police"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"


class NotificationType(str, enum.Enum):
    FOLLOW = "follow"
    LIKE = "like"
    COMMENT = "comment"
    DOCTOR_APPROVED = "doctor_approved"
    DOCTOR_REJECTED = "doctor_rejected"
    SOS_ALERT = "sos_alert"
    COMPLAINT_UPDATE = "complaint_update"


class SOSStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
