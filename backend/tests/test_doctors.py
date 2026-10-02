from tests.conftest import signup_and_login


def _create_doctor_profile(client, headers, registration_number="MCI-0001"):
    return client.post(
        "/api/v1/doctors/profile",
        headers=headers,
        json={
            "specialization": "Cardiology",
            "registration_number": registration_number,
            "registration_council": "MCI",
            "years_of_experience": 5,
        },
    )


def test_create_profile_promotes_role_to_doctor(client):
    headers = signup_and_login(client, email="doc@example.com", username="doc1", full_name="Doc One")
    r = _create_doctor_profile(client, headers)
    assert r.status_code == 201
    assert r.json()["verification_status"] == "pending"

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["role"] == "doctor"


def test_duplicate_profile_for_same_user_rejected(client):
    headers = signup_and_login(client, email="doc2@example.com", username="doc2", full_name="Doc Two")
    _create_doctor_profile(client, headers, registration_number="MCI-0002")
    r = _create_doctor_profile(client, headers, registration_number="MCI-9999")
    assert r.status_code == 409


def test_unverified_doctor_hidden_from_public_search(client):
    headers = signup_and_login(client, email="doc3@example.com", username="doc3", full_name="Doc Three")
    _create_doctor_profile(client, headers, registration_number="MCI-0003")

    r = client.get("/api/v1/doctors?specialization=Cardiology")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_approval_flow(client, make_admin):
    headers = signup_and_login(client, email="doc4@example.com", username="doc4", full_name="Doc Four")
    profile = _create_doctor_profile(client, headers, registration_number="MCI-0004").json()

    admin_email, admin_password = make_admin()
    r = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_password})
    admin_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.get("/api/v1/doctors/admin/pending", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.post(
        f"/api/v1/doctors/admin/{profile['id']}/verify",
        headers=admin_headers,
        json={"approve": True, "notes": "Verified credentials"},
    )
    assert r.status_code == 200
    assert r.json()["verification_status"] == "approved"

    r = client.get("/api/v1/doctors?specialization=Cardiology")
    assert len(r.json()) == 1


def test_non_admin_cannot_access_pending_queue(client):
    headers = signup_and_login(client, email="doc5@example.com", username="doc5", full_name="Doc Five")
    r = client.get("/api/v1/doctors/admin/pending", headers=headers)
    assert r.status_code == 403
