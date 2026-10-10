from tests.conftest import signup_and_login


def test_signup_creates_unverified_patient(client):
    r = client.post(
        "/api/v1/auth/signup",
        json={"email": "a@example.com", "password": "testpass123", "full_name": "A B", "username": "aone"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "patient"
    assert body["is_email_verified"] is False


def test_duplicate_email_signup_rejected(client):
    payload = {"email": "dup@example.com", "password": "testpass123", "full_name": "Dup", "username": "dupuser"}
    client.post("/api/v1/auth/signup", json=payload)
    r = client.post("/api/v1/auth/signup", json={**payload, "username": "dupuser2"})
    assert r.status_code == 409


def test_weak_password_rejected(client):
    r = client.post(
        "/api/v1/auth/signup",
        json={"email": "weak@example.com", "password": "onlyletters", "full_name": "W", "username": "weakuser"},
    )
    assert r.status_code == 422  # missing digit


def test_login_wrong_password_401(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "b@example.com", "password": "testpass123", "full_name": "B", "username": "buser"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "b@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token(client):
    headers = signup_and_login(client, email="c@example.com", username="cuser", full_name="C")
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "cuser"


def test_refresh_token_issues_new_access_token(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "d@example.com", "password": "testpass123", "full_name": "D", "username": "duser"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "d@example.com", "password": "testpass123"})
    refresh_token = r.json()["refresh_token"]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()
