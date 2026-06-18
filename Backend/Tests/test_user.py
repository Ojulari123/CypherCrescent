import tables
from conftest import SAMPLE_USER, auth, register, TestSession
from Utils.email_token import create_email_verification_token
from Utils.security import create_password_reset_token

# Register / Login / Refresh
class TestAuth:
    def test_register_returns_token_and_user(self, client):
        body = register(client)
        assert "access_token" in body
        assert body["user"]["email"] == SAMPLE_USER["email"]
        assert body["user"]["email_verified"] is False

    def test_register_triggers_verification_email(self, client, patch_external_io):
        register(client)
        patch_external_io["send_verification"].assert_called_once()

    def test_register_without_display_name_succeeds(self, client):
        payload = {k: v for k, v in SAMPLE_USER.items() if k != "display_name"}
        r = client.post("/api/users/register", json=payload)
        assert r.status_code == 201
        assert r.json()["user"]["display_name"] is None

    def test_register_duplicate_email_409(self, client):
        register(client)
        r = client.post("/api/users/register", json=SAMPLE_USER)
        assert r.status_code == 409

    def test_register_weak_password_400(self, client):
        bad = {**SAMPLE_USER, "password": "alllower1!"}  # missing uppercase
        r = client.post("/api/users/register", json=bad)
        assert r.status_code == 400

    def test_login_success(self, client):
        register(client)
        r = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password_401(self, client):
        register(client)
        r = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": "Wrong123!"},
        )
        assert r.status_code == 401

    def test_login_unknown_email_401(self, client):
        r = client.post(
            "/api/users/login",
            json={"email": "nobody@example.com", "password": "Anything1!"},
        )
        assert r.status_code == 401

    def test_refresh_returns_new_token(self, client):
        body = register(client)
        r = client.post("/api/users/refresh", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert "access_token" in r.json()

# /me Tests
class TestMe:
    def test_get_me(self, client):
        body = register(client)
        r = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json()["email"] == SAMPLE_USER["email"]

    def test_get_me_unauthorized(self, client):
        r = client.get("/api/users/me")
        assert r.status_code == 401

    def test_update_name(self, client):
        body = register(client)
        r = client.patch(
            "/api/users/me",
            json={"first_name": "Alicia"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert r.json()["first_name"] == "Alicia"

    def test_update_email_clears_verification_and_triggers_email(self, client, patch_external_io):
        body = register(client)
        patch_external_io["send_verification"].reset_mock()

        r = client.patch(
            "/api/users/me",
            json={"email": "alice2@example.com"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert r.json()["email"] == "alice2@example.com"
        assert r.json()["email_verified"] is False
        patch_external_io["send_verification"].assert_called_once()

    def test_update_email_clash_409(self, client):
        register(client)
        body2 = register(client, {**SAMPLE_USER, "email": "bob@example.com"})
        r = client.patch(
            "/api/users/me",
            json={"email": SAMPLE_USER["email"]},
            headers=auth(body2["access_token"]),
        )
        assert r.status_code == 409


# ────────────────────────────────────────────────────────────────────
# Password change
# ────────────────────────────────────────────────────────────────────
class TestPasswordChange:
    def test_change_password_returns_fresh_token_and_invalidates_old(self, client, patch_external_io):
        body = register(client)
        old_token = body["access_token"]

        # Step 1: triggers an emailed code, does not change the password yet
        r = client.put(
            "/api/users/me/password",
            json={"current_password": SAMPLE_USER["password"], "new_password": "NewSecret123!"},
            headers=auth(old_token),
        )
        assert r.status_code == 200
        assert r.json()["two_factor_required"] is True
        assert "access_token" not in r.json()
        # Old token still valid until the change is confirmed
        assert client.get("/api/users/me", headers=auth(old_token)).status_code == 200

        # Step 2: confirm with the emailed code
        code = patch_external_io["two_factor"].call_args.args[2]
        r2 = client.put(
            "/api/users/me/password/verify",
            json={"code": code, "new_password": "NewSecret123!"},
            headers=auth(old_token),
        )
        assert r2.status_code == 200
        new_token = r2.json()["access_token"]

        # Old token now stale (token_version bumped); new token works
        assert client.get("/api/users/me", headers=auth(old_token)).status_code == 401
        assert client.get("/api/users/me", headers=auth(new_token)).status_code == 200

    def test_change_password_wrong_current_401(self, client):
        body = register(client)
        r = client.put(
            "/api/users/me/password",
            json={"current_password": "Wrong123!", "new_password": "NewSecret123!"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 401

    def test_change_password_weak_new_400(self, client):
        body = register(client)
        r = client.put(
            "/api/users/me/password",
            json={"current_password": SAMPLE_USER["password"], "new_password": "alllower1!"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 400

    def test_change_password_same_as_current_400(self, client):
        body = register(client)
        r = client.put(
            "/api/users/me/password",
            json={"current_password": SAMPLE_USER["password"], "new_password": SAMPLE_USER["password"]},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 400

# Logout
class TestLogout:
    def test_logout_invalidates_token(self, client):
        body = register(client)
        r = client.post("/api/users/logout", headers=auth(body["access_token"]))
        assert r.status_code == 200
        r2 = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert r2.status_code == 401

    def test_logout_all_invalidates_token(self, client):
        body = register(client)
        r = client.post("/api/users/logout-all", headers=auth(body["access_token"]))
        assert r.status_code == 200
        r2 = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert r2.status_code == 401

# Email verification flows
class TestEmailFlows:
    def test_verify_with_valid_token_marks_user_verified(self, client):
        body = register(client)
        token = create_email_verification_token(SAMPLE_USER["email"])
        r = client.get("/api/users/verify-email", params={"token": token})
        assert r.status_code == 200

        me = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert me.json()["email_verified"] is True

    def test_verify_with_access_token_rejected_400(self, client):
        body = register(client)
        r = client.get("/api/users/verify-email", params={"token": body["access_token"]})
        assert r.status_code == 400

    def test_verify_with_garbage_token_400(self, client):
        r = client.get("/api/users/verify-email", params={"token": "not-a-jwt"})
        assert r.status_code == 400

    def test_resend_verification_known_email(self, client, patch_external_io):
        register(client)
        patch_external_io["send_verification"].reset_mock()
        r = client.post("/api/users/resend-verification", json={"email": SAMPLE_USER["email"]})
        assert r.status_code == 200
        patch_external_io["send_verification"].assert_called_once()

    def test_resend_verification_unknown_email_silent_200(self, client, patch_external_io):
        r = client.post("/api/users/resend-verification", json={"email": "nobody@example.com"})
        assert r.status_code == 200
        patch_external_io["send_verification"].assert_not_called()

    def test_resend_verification_already_verified_does_not_leak(self, client, patch_external_io):
        register(client)
        token = create_email_verification_token(SAMPLE_USER["email"])
        client.get("/api/users/verify-email", params={"token": token})

        patch_external_io["send_verification"].reset_mock()
        r = client.post("/api/users/resend-verification", json={"email": SAMPLE_USER["email"]})
        assert r.status_code == 200  # same response as unknown/unverified — no enumeration
        patch_external_io["send_verification"].assert_not_called()


    def test_forgot_password_known_email_triggers_reset(self, client, patch_external_io):
        register(client)
        r = client.post("/api/users/forgot-password", json={"email": SAMPLE_USER["email"]})
        assert r.status_code == 200
        patch_external_io["send_password_reset"].assert_called_once()

    def test_forgot_password_unknown_email_silent_200(self, client, patch_external_io):
        r = client.post("/api/users/forgot-password", json={"email": "nobody@example.com"})
        assert r.status_code == 200
        patch_external_io["send_password_reset"].assert_not_called()

    def test_reset_password_with_valid_token_updates_password(self, client):
        register(client)
        token = create_password_reset_token(SAMPLE_USER["email"])
        r = client.post(
            "/api/users/reset-password",
            json={"token": token, "new_password": "FreshPass123!"},
        )
        assert r.status_code == 200

        # Old password no longer works
        r1 = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": SAMPLE_USER["password"]},
        )
        assert r1.status_code == 401
        # New password does
        r2 = client.post(
            "/api/users/login",
            json={"email": SAMPLE_USER["email"], "password": "FreshPass123!"},
        )
        assert r2.status_code == 200

    def test_reset_password_with_email_verification_token_rejected(self, client):
        register(client)
        wrong = create_email_verification_token(SAMPLE_USER["email"])
        r = client.post(
            "/api/users/reset-password",
            json={"token": wrong, "new_password": "FreshPass123!"},
        )
        assert r.status_code == 400

    def test_reset_password_same_as_current_400(self, client):
        register(client)
        token = create_password_reset_token(SAMPLE_USER["email"])
        r = client.post(
            "/api/users/reset-password",
            json={"token": token, "new_password": SAMPLE_USER["password"]},
        )
        assert r.status_code == 400

    def test_reset_password_token_is_single_use(self, client):
        register(client)  # new user -> token_version 0
        token = create_password_reset_token(SAMPLE_USER["email"])

        r1 = client.post(
            "/api/users/reset-password",
            json={"token": token, "new_password": "FreshPass123!"},
        )
        assert r1.status_code == 200

        # Reusing the same token after a successful reset is rejected (token_version bumped)
        r2 = client.post(
            "/api/users/reset-password",
            json={"token": token, "new_password": "EvenFresher123!"},
        )
        assert r2.status_code == 400

# Profile photo
class TestProfilePhoto:
    def test_upload_returns_url_and_stores_on_user(self, client, patch_external_io):
        body = register(client)
        files = {"file": ("avatar.jpg", b"fakejpegbytes", "image/jpeg")}
        r = client.post(
            "/api/users/me/profile-photo",
            files=files,
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert r.json()["profile_photo_url"].startswith("https://")
        patch_external_io["upload"].assert_called_once()

        me = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert me.json()["profile_photo_url"] is not None

    def test_upload_invalid_mime_400(self, client):
        body = register(client)
        files = {"file": ("doc.pdf", b"%PDF", "application/pdf")}
        r = client.post(
            "/api/users/me/profile-photo",
            files=files,
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 400

    def test_upload_replaces_previous_photo(self, client, patch_external_io):
        body = register(client)
        files = {"file": ("a.jpg", b"x", "image/jpeg")}

        client.post("/api/users/me/profile-photo", files=files, headers=auth(body["access_token"]))
        client.post("/api/users/me/profile-photo", files=files, headers=auth(body["access_token"]))

        # Second upload should have deleted the first photo
        assert patch_external_io["delete"].call_count >= 1
        assert patch_external_io["upload"].call_count == 2

    def test_delete_when_none_400(self, client):
        body = register(client)
        r = client.delete("/api/users/me/profile-photo", headers=auth(body["access_token"]))
        assert r.status_code == 400

    def test_delete_clears_photo(self, client, patch_external_io):
        body = register(client)
        files = {"file": ("a.jpg", b"x", "image/jpeg")}
        client.post("/api/users/me/profile-photo", files=files, headers=auth(body["access_token"]))

        r = client.delete("/api/users/me/profile-photo", headers=auth(body["access_token"]))
        assert r.status_code == 200
        patch_external_io["delete"].assert_called()

        me = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert me.json()["profile_photo_url"] is None

# Delete account (cascade)
class TestDeleteAccount:
    def test_wrong_password_401(self, client):
        body = register(client)
        r = client.request(
            "DELETE",
            "/api/users/me",
            json={"password": "Wrong123!"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 401

    def test_success_removes_user_and_invalidates_token(self, client):
        body = register(client)
        r = client.request(
            "DELETE",
            "/api/users/me",
            json={"password": SAMPLE_USER["password"]},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200

        # Token now points at a non-existent user
        r2 = client.get("/api/users/me", headers=auth(body["access_token"]))
        assert r2.status_code == 401

    def test_cascade_cleans_holdings_and_watchlist(self, client):
        body = register(client)

        # Seed a holding + watchlist row directly via the test session
        with TestSession() as db:
            user = db.query(tables.User).first()
            db.add(tables.Holding(user_id=user.id, coin_slug="btc", quantity=1, buy_price=50000))
            db.add(tables.Watchlist(user_id=user.id, coin_slug="eth"))
            db.commit()

        client.request(
            "DELETE",
            "/api/users/me",
            json={"password": SAMPLE_USER["password"]},
            headers=auth(body["access_token"]),
        )

        with TestSession() as db:
            assert db.query(tables.User).count() == 0
            assert db.query(tables.Holding).count() == 0
            assert db.query(tables.Watchlist).count() == 0

    def test_cascade_deletes_cloudinary_photo(self, client, patch_external_io):
        body = register(client)
        files = {"file": ("a.jpg", b"x", "image/jpeg")}
        client.post("/api/users/me/profile-photo", files=files, headers=auth(body["access_token"]))

        patch_external_io["cascade_delete"].reset_mock()
        client.request(
            "DELETE",
            "/api/users/me",
            json={"password": SAMPLE_USER["password"]},
            headers=auth(body["access_token"]),
        )
        patch_external_io["cascade_delete"].assert_called_once()
