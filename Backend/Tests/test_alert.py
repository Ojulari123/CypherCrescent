from unittest.mock import patch, MagicMock
import pytest
from conftest import auth, register
from tables import PriceAlert
from conftest import TestSession
from Utils.coingecko import MarketDataError

OTHER_USER = {
    "email": "bob@example.com",
    "password": "Secret123!",
    "first_name": "Bob",
    "last_name": "Smith",
    "display_name": "bob",
}

SAMPLE_MARKETS = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "image": "https://example.com/btc.png",
        "current_price": 70000,
        "market_cap": 1_300_000_000_000,
        "price_change_percentage_24h": 2.34,
    },
]

@pytest.fixture(autouse=True)
def _stub_coin_validation():
    with patch("Utils.coingecko.get_markets", side_effect=lambda ids: [{"id": c} for c in ids]):
        yield


def create_alert(client, token, coin_slug="bitcoin", target_price=60000, direction="above"):
    r = client.post(
        "/api/alerts",
        json={"coin_slug": coin_slug, "target_price": target_price, "direction": direction},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateAlert:
    def test_create_success(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 60000, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["coin_slug"] == "bitcoin"
        assert data["direction"] == "above"
        assert data["triggered"] is False
        assert data["triggered_at"] is None
        assert "id" in data

    def test_create_below_direction(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 30000, "direction": "below"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 201
        assert r.json()["direction"] == "below"

    def test_create_normalizes_slug(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "  BiTcOiN  ", "target_price": 60000, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 201
        assert r.json()["coin_slug"] == "bitcoin"

    def test_create_unauthenticated_401(self, client):
        r = client.post("/api/alerts", json={"coin_slug": "bitcoin", "target_price": 60000, "direction": "above"})
        assert r.status_code == 401

    def test_create_negative_price_422(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": -1, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_create_zero_price_422(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 0, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_create_empty_slug_422(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "   ", "target_price": 60000, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_create_invalid_direction_422(self, client):
        body = register(client)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 60000, "direction": "sideways"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_create_unrecognized_coin_400(self, client):
        body = register(client)
        with patch("Utils.coingecko.get_markets", return_value=[]):
            r = client.post(
                "/api/alerts",
                json={"coin_slug": "notarealcoin", "target_price": 1, "direction": "above"},
                headers=auth(body["access_token"]),
            )
        assert r.status_code == 400

    def test_create_enforces_limit(self, client):
        body = register(client)
        for i in range(10):
            create_alert(client, body["access_token"], target_price=1000 + i)
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 99999, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 400
        assert "10" in r.json()["detail"]

    def test_triggered_alerts_dont_count_toward_limit(self, client):
        body = register(client)
        # Fill up with 10 active alerts
        for i in range(10):
            create_alert(client, body["access_token"], target_price=1000 + i)
        # Manually mark all as triggered
        db = TestSession()
        db.query(PriceAlert).update({"triggered": True})
        db.commit()
        db.close()
        # Should now be able to create a new one
        r = client.post(
            "/api/alerts",
            json={"coin_slug": "bitcoin", "target_price": 99999, "direction": "above"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 201


# ── List ──────────────────────────────────────────────────────────────────────

class TestListAlerts:
    def test_list_empty(self, client):
        body = register(client)
        r = client.get("/api/alerts", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_created_alert(self, client):
        body = register(client)
        create_alert(client, body["access_token"])
        r = client.get("/api/alerts", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["coin_slug"] == "bitcoin"

    def test_list_only_own_alerts(self, client):
        alice = register(client)
        create_alert(client, alice["access_token"])
        bob = register(client, OTHER_USER)
        r = client.get("/api/alerts", headers=auth(bob["access_token"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_unauthenticated_401(self, client):
        r = client.get("/api/alerts")
        assert r.status_code == 401

    def test_list_includes_triggered_alerts(self, client):
        body = register(client)
        create_alert(client, body["access_token"])
        db = TestSession()
        db.query(PriceAlert).update({"triggered": True})
        db.commit()
        db.close()
        r = client.get("/api/alerts", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json()[0]["triggered"] is True


# ── Edit ──────────────────────────────────────────────────────────────────────

class TestEditAlert:
    def test_edit_target_price(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"target_price": 75000},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert float(r.json()["target_price"]) == 75000

    def test_edit_direction(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"], direction="above")
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"direction": "below"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert r.json()["direction"] == "below"

    def test_edit_both_fields(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"target_price": 80000, "direction": "below"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert float(data["target_price"]) == 80000
        assert data["direction"] == "below"

    def test_edit_partial_empty_body_is_noop(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"], target_price=60000, direction="above")
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert float(data["target_price"]) == 60000
        assert data["direction"] == "above"

    def test_cannot_edit_triggered_alert(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        db = TestSession()
        db.query(PriceAlert).filter(PriceAlert.id == alert["id"]).update({"triggered": True})
        db.commit()
        db.close()
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"target_price": 99999},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 400

    def test_edit_missing_alert_404(self, client):
        body = register(client)
        r = client.patch("/api/alerts/9999", json={"target_price": 50000}, headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_cannot_edit_another_users_alert(self, client):
        alice = register(client)
        alert = create_alert(client, alice["access_token"])
        bob = register(client, OTHER_USER)
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"target_price": 99999},
            headers=auth(bob["access_token"]),
        )
        assert r.status_code == 404

    def test_edit_negative_price_422(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        r = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"target_price": -1},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_edit_unauthenticated_401(self, client):
        r = client.patch("/api/alerts/1", json={"target_price": 50000})
        assert r.status_code == 401


# ── Reactivate ────────────────────────────────────────────────────────────────

class TestReactivateAlert:
    def _trigger(self, alert_id):
        db = TestSession()
        db.query(PriceAlert).filter(PriceAlert.id == alert_id).update({"triggered": True, "triggered_at": "2026-06-01T00:00:00"})
        db.commit()
        db.close()

    def test_reactivate_success(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        self._trigger(alert["id"])
        r = client.post(f"/api/alerts/{alert['id']}/reactivate", headers=auth(body["access_token"]))
        assert r.status_code == 200
        data = r.json()
        assert data["triggered"] is False
        assert data["triggered_at"] is None

    def test_reactivate_already_active_400(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        r = client.post(f"/api/alerts/{alert['id']}/reactivate", headers=auth(body["access_token"]))
        assert r.status_code == 400
        assert "already active" in r.json()["detail"]

    def test_reactivate_enforces_limit(self, client):
        body = register(client)
        # Create 10 active + 1 triggered
        for i in range(10):
            create_alert(client, body["access_token"], target_price=1000 + i)
        extra = create_alert(client, body["access_token"], target_price=999)
        self._trigger(extra["id"])
        # All 10 slots now taken by active — reactivate should fail
        # First mark extra as triggered but the 10 active remain
        r = client.post(f"/api/alerts/{extra['id']}/reactivate", headers=auth(body["access_token"]))
        assert r.status_code == 400
        assert "10" in r.json()["detail"]

    def test_reactivate_missing_404(self, client):
        body = register(client)
        r = client.post("/api/alerts/9999/reactivate", headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_cannot_reactivate_another_users_alert(self, client):
        alice = register(client)
        alert = create_alert(client, alice["access_token"])
        self._trigger(alert["id"])
        bob = register(client, OTHER_USER)
        r = client.post(f"/api/alerts/{alert['id']}/reactivate", headers=auth(bob["access_token"]))
        assert r.status_code == 404

    def test_reactivate_unauthenticated_401(self, client):
        r = client.post("/api/alerts/1/reactivate")
        assert r.status_code == 401


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeleteAlert:
    def test_delete_success(self, client):
        body = register(client)
        alert = create_alert(client, body["access_token"])
        r = client.delete(f"/api/alerts/{alert['id']}", headers=auth(body["access_token"]))
        assert r.status_code == 200
        r = client.get("/api/alerts", headers=auth(body["access_token"]))
        assert r.json() == []

    def test_delete_missing_404(self, client):
        body = register(client)
        r = client.delete("/api/alerts/9999", headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_cannot_delete_another_users_alert(self, client):
        alice = register(client)
        alert = create_alert(client, alice["access_token"])
        bob = register(client, OTHER_USER)
        r = client.delete(f"/api/alerts/{alert['id']}", headers=auth(bob["access_token"]))
        assert r.status_code == 404

    def test_delete_unauthenticated_401(self, client):
        r = client.delete("/api/alerts/1")
        assert r.status_code == 401


# ── Checker ───────────────────────────────────────────────────────────────────

class TestAlertChecker:
    def _make_alert(self, user_id, coin_slug, target_price, direction):
        db = TestSession()
        alert = PriceAlert(
            user_id=user_id,
            coin_slug=coin_slug,
            target_price=target_price,
            direction=direction,
        )
        db.add(alert)
        db.commit()
        alert_id = alert.id
        db.close()
        return alert_id

    def _get_alert(self, alert_id):
        db = TestSession()
        alert = db.get(PriceAlert, alert_id)
        triggered = alert.triggered
        triggered_at = alert.triggered_at
        db.close()
        return triggered, triggered_at

    def test_checker_triggers_above(self, client):
        body = register(client)
        user_id = client.get("/api/users/me", headers=auth(body["access_token"])).json()["id"]
        alert_id = self._make_alert(user_id, "bitcoin", 60000, "above")

        with patch("Utils.alert_checker.get_markets", return_value=[{"id": "bitcoin", "name": "Bitcoin", "current_price": 70000}]), \
             patch("Utils.alert_checker.send_price_alert_email") as mock_email:
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()

        triggered, triggered_at = self._get_alert(alert_id)
        assert triggered is True
        assert triggered_at is not None
        mock_email.assert_called_once()

    def test_checker_triggers_below(self, client):
        body = register(client)
        user_id = client.get("/api/users/me", headers=auth(body["access_token"])).json()["id"]
        alert_id = self._make_alert(user_id, "bitcoin", 60000, "below")

        with patch("Utils.alert_checker.get_markets", return_value=[{"id": "bitcoin", "name": "Bitcoin", "current_price": 50000}]), \
             patch("Utils.alert_checker.send_price_alert_email") as mock_email:
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()

        triggered, triggered_at = self._get_alert(alert_id)
        assert triggered is True
        assert triggered_at is not None
        mock_email.assert_called_once()

    def test_checker_does_not_trigger_when_condition_not_met(self, client):
        body = register(client)
        user_id = client.get("/api/users/me", headers=auth(body["access_token"])).json()["id"]
        alert_id = self._make_alert(user_id, "bitcoin", 80000, "above")

        with patch("Utils.alert_checker.get_markets", return_value=[{"id": "bitcoin", "name": "Bitcoin", "current_price": 70000}]), \
             patch("Utils.alert_checker.send_price_alert_email") as mock_email:
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()

        triggered, _ = self._get_alert(alert_id)
        assert triggered is False
        mock_email.assert_not_called()

    def test_checker_skips_when_no_active_alerts(self, client):
        register(client)
        with patch("Utils.alert_checker.get_markets") as mock_cg:
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()
        mock_cg.assert_not_called()

    def test_checker_handles_coingecko_down(self, client):
        body = register(client)
        user_id = client.get("/api/users/me", headers=auth(body["access_token"])).json()["id"]
        alert_id = self._make_alert(user_id, "bitcoin", 60000, "above")

        with patch("Utils.alert_checker.get_markets", side_effect=MarketDataError("down")), \
             patch("Utils.alert_checker.send_price_alert_email") as mock_email:
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()

        triggered, _ = self._get_alert(alert_id)
        assert triggered is False
        mock_email.assert_not_called()

    def test_checker_email_failure_does_not_block_other_alerts(self, client):
        body = register(client)
        user_id = client.get("/api/users/me", headers=auth(body["access_token"])).json()["id"]
        alert1_id = self._make_alert(user_id, "bitcoin", 60000, "above")
        alert2_id = self._make_alert(user_id, "bitcoin", 60000, "above")

        call_count = 0
        def flaky_email(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("SMTP flaked")

        with patch("Utils.alert_checker.get_markets", return_value=[{"id": "bitcoin", "name": "Bitcoin", "current_price": 70000}]), \
             patch("Utils.alert_checker.send_price_alert_email", side_effect=flaky_email):
            from Utils.alert_checker import check_price_alerts
            check_price_alerts()

        # Both alerts should still be marked triggered despite email failure on first
        triggered1, _ = self._get_alert(alert1_id)
        triggered2, _ = self._get_alert(alert2_id)
        assert triggered1 is True
        assert triggered2 is True
