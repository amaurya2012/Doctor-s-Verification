"""Import every model so Base.metadata has all tables (needed by Alembic and create_all)."""
from app.db.base import Base  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.doctor_profile import DoctorProfile  # noqa: F401
from app.models.certificate import Certificate  # noqa: F401
from app.models.retired_police_profile import RetiredPoliceProfile  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.like import Like  # noqa: F401
from app.models.follow import Follow  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.sos_incident import SOSIncident  # noqa: F401
from app.models.complaint import Complaint  # noqa: F401

__all__ = [
    "Base", "User", "DoctorProfile", "Certificate", "RetiredPoliceProfile",
    "Post", "Comment", "Like", "Follow", "Notification", "SOSIncident", "Complaint",
]
