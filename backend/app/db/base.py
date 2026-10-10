"""
SQLAlchemy 2.0 declarative base and session factory.
"""
from datetime import datetime, timezone

from sqlalchemy import create_engine, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

database_url = settings.sqlalchemy_database_url
is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# On serverless (Vercel) each invocation can be a fresh process, so a
# persistent pool just piles up connections. NullPool opens/closes per
# checkout; use a pooled DB endpoint (e.g. Neon's pooler) for real pooling.
poolclass = NullPool if not is_sqlite else None

engine = create_engine(
    database_url,
    connect_args=connect_args,
    poolclass=poolclass,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models, with shared timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def get_db():
    """FastAPI dependency: yields a DB session and ensures it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
