"""Auth business logic: signup, login, Google OAuth, tokens, email verification."""
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_email_verification_token,
    decode_token_of_type,
)
from app.models.enums import AuthProvider
from app.models.user import User

settings = get_settings()


class AuthError(Exception):
    """Raised for any auth failure the route layer should turn into an HTTP error."""


def signup(db: Session, *, email: str, password: str, full_name: str, username: str) -> tuple[User, str]:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        auth_provider=AuthProvider.LOCAL,
        full_name=full_name,
        username=username,
        is_email_verified=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AuthError("Email or username already registered")
    db.refresh(user)

    verification_token = create_email_verification_token(subject=str(user.id))
    return user, verification_token


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or user.hashed_password is None:
        raise AuthError("Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise AuthError("Incorrect email or password")
    if not user.is_active:
        raise AuthError("Account is deactivated")
    return user


def authenticate_with_google(db: Session, *, id_token_str: str) -> User:
    try:
        idinfo = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise AuthError("Invalid Google token")

    google_sub = idinfo["sub"]
    email = idinfo.get("email", "").lower()
    full_name = idinfo.get("name", email.split("@")[0])
    avatar_url = idinfo.get("picture")

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user is not None:
        return user

    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        user.google_sub = google_sub
        if user.auth_provider == AuthProvider.LOCAL and user.hashed_password is None:
            user.auth_provider = AuthProvider.GOOGLE
        db.commit()
        db.refresh(user)
        return user

    base_username = email.split("@")[0][:40]
    username = base_username
    suffix = 1
    while db.query(User).filter(User.username == username).first() is not None:
        suffix += 1
        username = f"{base_username}{suffix}"

    user = User(
        email=email,
        hashed_password=None,
        auth_provider=AuthProvider.GOOGLE,
        google_sub=google_sub,
        full_name=full_name,
        username=username,
        avatar_url=avatar_url,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    subject = str(user.id)
    return create_access_token(subject), create_refresh_token(subject)


def refresh_access_token(db: Session, *, refresh_token: str) -> str:
    try:
        payload = decode_token_of_type(refresh_token, expected_type="refresh")
    except JWTError:
        raise AuthError("Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise AuthError("Invalid refresh token")

    return create_access_token(subject=str(user.id))


def verify_email(db: Session, *, token: str) -> User:
    try:
        payload = decode_token_of_type(token, expected_type="email_verification")
    except JWTError:
        raise AuthError("Invalid or expired verification token")

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if user is None:
        raise AuthError("User not found")

    user.is_email_verified = True
    db.commit()
    db.refresh(user)
    return user
