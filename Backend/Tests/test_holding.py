from decimal import Decimal
from conftest import SAMPLE_USER, auth, register

SAMPLE_HOLDING = {
    "coin_slug": "bitcoin",
    "quantity": "0.5",
    "buy_price": "65000",
}

OTHER_USER = {
    "email": "bob@example.com",
    "password": "Secret123!",
    "first_name": "Bob",
    "last_name": "Smith",
    "display_name": "bob",
}

def add_sample_holding(client, token, payload=None):
    body = payload or SAMPLE_HOLDING
    r = client.post("/api/holdings", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# Add holding
class TestAddHolding:
    def test_add_success(self, client):
        body = register(client)
        r = client.post("/api/holdings", json=SAMPLE_HOLDING, headers=auth(body["access_token"]))
        assert r.status_code == 201
        assert r.json()["coin_slug"] == "bitcoin"
        assert Decimal(r.json()["quantity"]) == Decimal("0.5")
        assert Decimal(r.json()["buy_price"]) == Decimal("65000")

    def test_add_normalizes_slug_lowercase_and_strip(self, client):
        body = register(client)
        r = client.post(
            "/api/holdings",
            json={**SAMPLE_HOLDING, "coin_slug": "  BiTcOiN  "},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 201
        assert r.json()["coin_slug"] == "bitcoin"

    def test_add_duplicate_coin_409(self, client):
        body = register(client)
        add_sample_holding(client, body["access_token"])
        r = client.post("/api/holdings", json=SAMPLE_HOLDING, headers=auth(body["access_token"]))
        assert r.status_code == 409

    def test_add_zero_quantity_422(self, client):
        body = register(client)
        r = client.post(
            "/api/holdings",
            json={**SAMPLE_HOLDING, "quantity": "0"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_add_negative_quantity_422(self, client):
        body = register(client)
        r = client.post(
            "/api/holdings",
            json={**SAMPLE_HOLDING, "quantity": "-1"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_add_zero_buy_price_422(self, client):
        body = register(client)
        r = client.post(
            "/api/holdings",
            json={**SAMPLE_HOLDING, "buy_price": "0"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_add_empty_slug_422(self, client):
        body = register(client)
        r = client.post(
            "/api/holdings",
            json={**SAMPLE_HOLDING, "coin_slug": "   "},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_add_unauthenticated_401(self, client):
        r = client.post("/api/holdings", json=SAMPLE_HOLDING)
        assert r.status_code == 401


# List holdings
class TestListHoldings:
    def test_list_empty(self, client):
        body = register(client)
        r = client.get("/api/holdings", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_only_own_holdings(self, client):
        alice = register(client)
        bob = register(client, OTHER_USER)

        add_sample_holding(client, alice["access_token"])
        add_sample_holding(
            client,
            bob["access_token"],
            payload={"coin_slug": "ethereum", "quantity": "2", "buy_price": "3000"},
        )

        r = client.get("/api/holdings", headers=auth(alice["access_token"]))
        assert r.status_code == 200
        slugs = [h["coin_slug"] for h in r.json()]
        assert slugs == ["bitcoin"]

    def test_list_orders_by_created_at_desc(self, client):
        body = register(client)
        add_sample_holding(client, body["access_token"], payload={"coin_slug": "bitcoin", "quantity": "1", "buy_price": "60000"})
        add_sample_holding(client, body["access_token"], payload={"coin_slug": "ethereum", "quantity": "2", "buy_price": "3000"})
        add_sample_holding(client, body["access_token"], payload={"coin_slug": "solana", "quantity": "100", "buy_price": "150"})

        r = client.get("/api/holdings", headers=auth(body["access_token"]))
        slugs = [h["coin_slug"] for h in r.json()]
        assert slugs == ["solana", "ethereum", "bitcoin"]

    def test_list_unauthenticated_401(self, client):
        r = client.get("/api/holdings")
        assert r.status_code == 401


# Get one holding
class TestGetHolding:
    def test_get_success(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.get(f"/api/holdings/{holding['id']}", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json()["coin_slug"] == "bitcoin"

    def test_get_not_found_404(self, client):
        body = register(client)
        r = client.get("/api/holdings/9999", headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_get_belonging_to_other_user_returns_404(self, client):
        alice = register(client)
        bob = register(client, OTHER_USER)
        alices_holding = add_sample_holding(client, alice["access_token"])

        r = client.get(f"/api/holdings/{alices_holding['id']}", headers=auth(bob["access_token"]))
        assert r.status_code == 404


# Update holding
class TestUpdateHolding:
    def test_update_quantity(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.patch(
            f"/api/holdings/{holding['id']}",
            json={"quantity": "1.25"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert Decimal(r.json()["quantity"]) == Decimal("1.25")
        assert Decimal(r.json()["buy_price"]) == Decimal("65000")  # unchanged

    def test_update_buy_price(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.patch(
            f"/api/holdings/{holding['id']}",
            json={"buy_price": "70000"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert Decimal(r.json()["buy_price"]) == Decimal("70000")

    def test_update_both(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.patch(
            f"/api/holdings/{holding['id']}",
            json={"quantity": "2", "buy_price": "55000"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert Decimal(r.json()["quantity"]) == Decimal("2")
        assert Decimal(r.json()["buy_price"]) == Decimal("55000")

    def test_update_empty_body_no_op(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.patch(
            f"/api/holdings/{holding['id']}",
            json={},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 200
        assert Decimal(r.json()["quantity"]) == Decimal("0.5")

    def test_update_zero_quantity_422(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])
        r = client.patch(
            f"/api/holdings/{holding['id']}",
            json={"quantity": "0"},
            headers=auth(body["access_token"]),
        )
        assert r.status_code == 422

    def test_update_other_users_holding_404(self, client):
        alice = register(client)
        bob = register(client, OTHER_USER)
        alices_holding = add_sample_holding(client, alice["access_token"])

        r = client.patch(
            f"/api/holdings/{alices_holding['id']}",
            json={"quantity": "999"},
            headers=auth(bob["access_token"]),
        )
        assert r.status_code == 404


# Delete holding
class TestDeleteHolding:
    def test_delete_success(self, client):
        body = register(client)
        holding = add_sample_holding(client, body["access_token"])

        r = client.delete(f"/api/holdings/{holding['id']}", headers=auth(body["access_token"]))
        assert r.status_code == 200

        r2 = client.get(f"/api/holdings/{holding['id']}", headers=auth(body["access_token"]))
        assert r2.status_code == 404

    def test_delete_not_found_404(self, client):
        body = register(client)
        r = client.delete("/api/holdings/9999", headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_delete_other_users_holding_404(self, client):
        alice = register(client)
        bob = register(client, OTHER_USER)
        alices_holding = add_sample_holding(client, alice["access_token"])

        r = client.delete(f"/api/holdings/{alices_holding['id']}", headers=auth(bob["access_token"]))
        assert r.status_code == 404

        # Alice's holding still exists
        r2 = client.get(f"/api/holdings/{alices_holding['id']}", headers=auth(alice["access_token"]))
        assert r2.status_code == 200
