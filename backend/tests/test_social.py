from tests.conftest import signup_and_login


def test_create_post_and_public_feed(client):
    headers = signup_and_login(client, email="alice@example.com", username="alice", full_name="Alice")
    r = client.post("/api/v1/posts", headers=headers, json={"content": "Hello world"})
    assert r.status_code == 201

    r = client.get("/api/v1/posts")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["liked_by_me"] is False


def test_like_is_idempotent_and_counted_once(client):
    alice = signup_and_login(client, email="alice2@example.com", username="alice2", full_name="Alice")
    bob = signup_and_login(client, email="bob2@example.com", username="bob2", full_name="Bob")

    post_id = client.post("/api/v1/posts", headers=alice, json={"content": "post"}).json()["id"]

    client.post(f"/api/v1/posts/{post_id}/like", headers=bob)
    client.post(f"/api/v1/posts/{post_id}/like", headers=bob)  # duplicate, should not error or double-count

    r = client.get(f"/api/v1/posts/{post_id}")
    assert r.json()["like_count"] == 1


def test_comment_notifies_post_author(client):
    alice = signup_and_login(client, email="alice3@example.com", username="alice3", full_name="Alice")
    bob = signup_and_login(client, email="bob3@example.com", username="bob3", full_name="Bob")

    post_id = client.post("/api/v1/posts", headers=alice, json={"content": "post"}).json()["id"]
    client.post(f"/api/v1/posts/{post_id}/comments", headers=bob, json={"content": "nice!"})

    r = client.get("/api/v1/notifications", headers=alice)
    types = [n["type"] for n in r.json()]
    assert "comment" in types


def test_self_follow_rejected(client):
    alice = signup_and_login(client, email="alice4@example.com", username="alice4", full_name="Alice")
    me = client.get("/api/v1/auth/me", headers=alice).json()
    r = client.post(f"/api/v1/users/{me['id']}/follow", headers=alice)
    assert r.status_code == 400


def test_only_owner_can_delete_post(client):
    alice = signup_and_login(client, email="alice5@example.com", username="alice5", full_name="Alice")
    bob = signup_and_login(client, email="bob5@example.com", username="bob5", full_name="Bob")

    post_id = client.post("/api/v1/posts", headers=alice, json={"content": "post"}).json()["id"]

    r = client.delete(f"/api/v1/posts/{post_id}", headers=bob)
    assert r.status_code == 403

    r = client.delete(f"/api/v1/posts/{post_id}", headers=alice)
    assert r.status_code == 204
