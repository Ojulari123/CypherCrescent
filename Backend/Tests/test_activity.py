from conftest import auth, register, SAMPLE_USER

OTHER_USER = {
    "email": "bob@example.com",
    "password": "Secret123!",
    "first_name": "Bob",
    "last_name": "Smith",
    "display_name": "bob",
}


def events(client, token):
    r = client.get("/api/users/activity", headers=auth(token))
    assert r.status_code == 200, r.text
    return [row["event"] for row in r.json()]


class TestActivityLog:
    def test_register_is_logged(self, client):
        body = register(client)
        assert "register" in events(client, body["access_token"])

    def test_login_is_logged(self, client):
        register(client)
        login = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert events(client, login.json()["access_token"]).count("login") == 1

    def test_logout_all_is_logged(self, client):
        body = register(client)
        token = body["access_token"]
        client.post("/api/users/logout-all", headers=auth(token))

        # token is now invalid; log in again and confirm the event was recorded
        login = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert "logout_all" in events(client, login.json()["access_token"])

    def test_newest_first_and_captures_request_metadata(self, client):
        body = register(client)
        token = body["access_token"]
        r = client.get("/api/users/activity", headers=auth(token))
        first = r.json()[0]
        assert first["event"] == "register"
        # request metadata is captured (TestClient reports a client host)
        assert "ip_address" in first and "user_agent" in first

    def test_activity_is_per_user(self, client):
        alice = register(client)
        bob = register(client, OTHER_USER)
        # Bob only sees his own events, never Alice's
        assert events(client, bob["access_token"]) == ["register"]
        assert len(events(client, alice["access_token"])) >= 1

    def test_activity_requires_auth_401(self, client):
        r = client.get("/api/users/activity")
        assert r.status_code == 401
