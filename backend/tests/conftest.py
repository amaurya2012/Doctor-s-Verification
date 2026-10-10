"""
Shared pytest fixtures: an isolated in-memory SQLite DB per test
(so tests never interfere with each other or a real dev DB) and a
TestClient wired to use it via FastAPI's dependency override.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base, get_db
import app.models  # noqa: F401  (register all tables on Base.metadata)
from app.main import app
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def signup_and_login(client: TestClient, *, email: str, username: str, full_name: str, password: str = "testpass123") -> dict:
    """Helper: signs up a user and returns Authorization headers."""
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "full_name": full_name, "username": username},
    )
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def make_admin(db_session):
    """Factory fixture: creates an admin user directly in the DB, returns (email, password)."""

    def _make_admin(email: str = "admin@example.com", username: str = "admin", password: str = "adminpass123"):
        admin = User(
            email=email,
            full_name="Admin",
            username=username,
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
            is_email_verified=True,
        )
        db_session.add(admin)
        db_session.commit()
        return email, password

    return _make_admin
