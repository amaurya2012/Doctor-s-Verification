from tests.conftest import signup_and_login


def test_only_admin_or_verified_police_can_view_open_sos_queue(client):
    citizen = signup_and_login(client, email="cit@example.com", username="citizen", full_name="Citizen")
    client.post("/api/v1/sos", headers=citizen, json={"latitude": 1.0, "longitude": 1.0})

    r = client.get("/api/v1/sos/open", headers=citizen)
    assert r.status_code == 403


def test_admin_can_respond_to_sos_and_reporter_gets_notified(client, make_admin):
    citizen = signup_and_login(client, email="cit2@example.com", username="citizen2", full_name="Citizen")
    incident_id = client.post(
        "/api/v1/sos", headers=citizen, json={"latitude": 1.0, "longitude": 1.0}
    ).json()["id"]

    admin_email, admin_password = make_admin()
    r = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_password})
    admin_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(f"/api/v1/sos/{incident_id}/respond", headers=admin_headers, json={"status": "acknowledged"})
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"
    assert r.json()["responder"]["username"] == "admin"

    r = client.get("/api/v1/notifications", headers=citizen)
    assert any(n["type"] == "sos_alert" for n in r.json())


def test_invalid_complaint_target_type_rejected(client):
    citizen = signup_and_login(client, email="cit3@example.com", username="citizen3", full_name="Citizen")
    r = client.post(
        "/api/v1/complaints",
        headers=citizen,
        json={"target_object_type": "not_a_real_type", "target_object_id": 1, "reason": "test"},
    )
    assert r.status_code == 400


def test_non_admin_cannot_list_all_complaints(client):
    citizen = signup_and_login(client, email="cit4@example.com", username="citizen4", full_name="Citizen")
    r = client.get("/api/v1/complaints/admin/all", headers=citizen)
    assert r.status_code == 403


def test_admin_resolve_complaint_flow(client, make_admin):
    citizen = signup_and_login(client, email="cit5@example.com", username="citizen5", full_name="Citizen")
    complaint_id = client.post(
        "/api/v1/complaints",
        headers=citizen,
        json={"target_object_type": "user", "target_object_id": 999, "reason": "spam"},
    ).json()["id"]

    admin_email, admin_password = make_admin()
    r = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_password})
    admin_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(
        f"/api/v1/complaints/admin/{complaint_id}/resolve",
        headers=admin_headers,
        json={"status": "resolved", "resolution_notes": "handled"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
