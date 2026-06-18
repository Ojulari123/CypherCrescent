from conftest import auth, register, SAMPLE_USER

def latest_code(patch_external_io):
    return patch_external_io["two_factor"].call_args.args[2]

def enable_2fa(client, token, patch_external_io):
    r = client.post("/api/users/2fa/enable", headers=auth(token))
    assert r.status_code == 200, r.text
    code = latest_code(patch_external_io)
    r = client.post("/api/users/2fa/enable/confirm", json={"code": code}, headers=auth(token))
    assert r.status_code == 200, r.text

# Enable / disable
class TestToggle2FA:
    def test_enable_flow_sets_flag(self, client, patch_external_io):
        body = register(client)
        token = body["access_token"]
        assert body["user"]["two_factor_enabled"] is False

        enable_2fa(client, token, patch_external_io)

        me = client.get("/api/users/me", headers=auth(token))
        assert me.json()["two_factor_enabled"] is True

    def test_enable_confirm_wrong_code_400(self, client, patch_external_io):
        body = register(client)
        token = body["access_token"]
        client.post("/api/users/2fa/enable", headers=auth(token))
        r = client.post("/api/users/2fa/enable/confirm", json={"code": "000000"}, headers=auth(token))
        assert r.status_code == 400

    def test_enable_when_already_enabled_400(self, client, patch_external_io):
        body = register(client)
        token = body["access_token"]
        enable_2fa(client, token, patch_external_io)
        r = client.post("/api/users/2fa/enable", headers=auth(token))
        assert r.status_code == 400

    def test_disable_flow_clears_flag(self, client, patch_external_io):
        body = register(client)
        token = body["access_token"]
        enable_2fa(client, token, patch_external_io)

        r = client.post("/api/users/2fa/disable", headers=auth(token))
        assert r.status_code == 200
        code = latest_code(patch_external_io)
        r = client.post("/api/users/2fa/disable/confirm", json={"code": code}, headers=auth(token))
        assert r.status_code == 200

        me = client.get("/api/users/me", headers=auth(token))
        assert me.json()["two_factor_enabled"] is False

    def test_disable_when_not_enabled_400(self, client):
        body = register(client)
        r = client.post("/api/users/2fa/disable", headers=auth(body["access_token"]))
        assert r.status_code == 400

    def test_enable_requires_auth_401(self, client):
        r = client.post("/api/users/2fa/enable")
        assert r.status_code == 401

# Login with 2FA
class TestLogin2FA:
    def test_login_returns_challenge_then_verify_returns_token(self, client, patch_external_io):
        body = register(client)
        enable_2fa(client, body["access_token"], patch_external_io)

        r = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert r.status_code == 200
        assert r.json()["two_factor_required"] is True
        assert "access_token" not in r.json()
        challenge = r.json()["challenge_token"]

        code = latest_code(patch_external_io)
        r2 = client.post("/api/users/2fa/verify", json={"challenge_token": challenge, "code": code})
        assert r2.status_code == 200
        assert "access_token" in r2.json()

        # the issued token actually works
        me = client.get("/api/users/me", headers=auth(r2.json()["access_token"]))
        assert me.status_code == 200

    def test_login_without_2fa_returns_token_directly(self, client):
        body = register(client)
        r = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert "two_factor_required" not in r.json()

    def test_verify_wrong_code_400(self, client, patch_external_io):
        body = register(client)
        enable_2fa(client, body["access_token"], patch_external_io)
        r = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        challenge = r.json()["challenge_token"]
        r2 = client.post("/api/users/2fa/verify", json={"challenge_token": challenge, "code": "000000"})
        assert r2.status_code == 400

    def test_verify_bad_challenge_400(self, client):
        r = client.post("/api/users/2fa/verify", json={"challenge_token": "not-a-jwt", "code": "123456"})
        assert r.status_code == 400

    def test_token_endpoint_rejected_when_2fa_enabled_403(self, client, patch_external_io):
        body = register(client)
        enable_2fa(client, body["access_token"], patch_external_io)
        r = client.post(
            "/api/users/token",
            data={"username": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert r.status_code == 403

# Password change always requires a code, even without 2FA enabled
class TestPasswordChangeAlwaysVerified:
    def test_change_password_requires_code(self, client, patch_external_io):
        body = register(client)
        token = body["access_token"]

        r = client.put(
            "/api/users/me/password",
            json={"current_password": SAMPLE_USER["password"], "new_password": "NewSecret123!"},
            headers=auth(token),
        )
        assert r.status_code == 200
        assert r.json()["two_factor_required"] is True

        code = latest_code(patch_external_io)
        r2 = client.put(
            "/api/users/me/password/verify",
            json={"code": code, "new_password": "NewSecret123!"},
            headers=auth(token),
        )
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    def test_change_password_verify_wrong_code_400(self, client):
        body = register(client)
        token = body["access_token"]
        client.put(
            "/api/users/me/password",
            json={"current_password": SAMPLE_USER["password"], "new_password": "NewSecret123!"},
            headers=auth(token),
        )
        r = client.put(
            "/api/users/me/password/verify",
            json={"code": "000000", "new_password": "NewSecret123!"},
            headers=auth(token),
        )
        assert r.status_code == 400
