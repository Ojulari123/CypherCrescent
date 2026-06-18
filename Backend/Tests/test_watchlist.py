from unittest.mock import patch
import pytest
from conftest import auth, register

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
    # Treat every requested slug as a real coin so add tests don't hit the CoinGecko network; the unrecognized-coin path is tested explicitly.
    with patch("Utils.coingecko.get_markets", side_effect=lambda ids: [{"id": c} for c in ids]):
        yield

def add_to_watchlist(client, token, coin_slug):
    r = client.post("/api/watchlist", json={"coin_slug": coin_slug}, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()

# Add to watchlist
class TestAddWatchlist:
    def test_add_success(self, client):
        body = register(client)
        r = client.post("/api/watchlist", json={"coin_slug": "bitcoin"}, headers=auth(body["access_token"]))
        assert r.status_code == 201
        assert r.json()["coin_slug"] == "bitcoin"
        assert "id" in r.json()

    def test_add_normalizes_slug(self, client):
        body = register(client)
        r = client.post("/api/watchlist", json={"coin_slug": "  BiTcOiN  "}, headers=auth(body["access_token"]))
        assert r.status_code == 201
        assert r.json()["coin_slug"] == "bitcoin"

    def test_add_duplicate_409(self, client):
        body = register(client)
        add_to_watchlist(client, body["access_token"], "bitcoin")
        r = client.post("/api/watchlist", json={"coin_slug": "bitcoin"}, headers=auth(body["access_token"]))
        assert r.status_code == 409

    def test_add_race_integrityerror_returns_409(self, client):
        from sqlalchemy.exc import IntegrityError
        body = register(client)
        with patch("sqlalchemy.orm.Session.commit", side_effect=IntegrityError("dup", {}, Exception("dup"))):
            r = client.post("/api/watchlist", json={"coin_slug": "bitcoin"}, headers=auth(body["access_token"]))
        assert r.status_code == 409

    def test_add_unrecognized_coin_400(self, client):
        body = register(client)
        with patch("Utils.coingecko.get_markets", return_value=[]):
            r = client.post("/api/watchlist", json={"coin_slug": "notarealcoin"}, headers=auth(body["access_token"]))
        assert r.status_code == 400

    def test_add_empty_slug_422(self, client):
        body = register(client)
        r = client.post("/api/watchlist", json={"coin_slug": "   "}, headers=auth(body["access_token"]))
        assert r.status_code == 422

    def test_add_unauthenticated_401(self, client):
        r = client.post("/api/watchlist", json={"coin_slug": "bitcoin"})
        assert r.status_code == 401

# View watchlist
class TestListWatchlist:
    def test_empty(self, client):
        body = register(client)
        r = client.get("/api/watchlist", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_enriched_with_market_data(self, client):
        body = register(client)
        add_to_watchlist(client, body["access_token"], "bitcoin")

        with patch("Utils.watchlist.get_markets", return_value=SAMPLE_MARKETS):
            r = client.get("/api/watchlist", headers=auth(body["access_token"]))

        assert r.status_code == 200
        item = r.json()[0]
        assert item["coin_slug"] == "bitcoin"
        assert item["name"] == "Bitcoin"
        assert item["symbol"] == "BTC"
        assert item["current_price"] == "70000"

    def test_list_degrades_when_coingecko_down(self, client):
        import httpx
        body = register(client)
        add_to_watchlist(client, body["access_token"], "bitcoin")

        with patch("Utils.watchlist.get_markets", side_effect=httpx.HTTPError("down")):
            r = client.get("/api/watchlist", headers=auth(body["access_token"]))

        assert r.status_code == 200
        item = r.json()[0]
        assert item["coin_slug"] == "bitcoin"
        assert item["current_price"] is None
        assert item["name"] is None

    def test_list_only_shows_own_items(self, client):
        alice = register(client)
        add_to_watchlist(client, alice["access_token"], "bitcoin")
        bob = register(client, OTHER_USER)

        with patch("Utils.watchlist.get_markets", return_value=[]):
            r = client.get("/api/watchlist", headers=auth(bob["access_token"]))
        assert r.status_code == 200
        assert r.json() == []

# Remove from watchlist
class TestRemoveWatchlist:
    def test_remove_success(self, client):
        body = register(client)
        item = add_to_watchlist(client, body["access_token"], "bitcoin")
        r = client.delete(f"/api/watchlist/{item['id']}", headers=auth(body["access_token"]))
        assert r.status_code == 200

        with patch("Utils.watchlist.get_markets", return_value=[]):
            r = client.get("/api/watchlist", headers=auth(body["access_token"]))
        assert r.json() == []

    def test_remove_missing_404(self, client):
        body = register(client)
        r = client.delete("/api/watchlist/9999", headers=auth(body["access_token"]))
        assert r.status_code == 404

    def test_cannot_remove_another_users_item(self, client):
        alice = register(client)
        item = add_to_watchlist(client, alice["access_token"], "bitcoin")
        bob = register(client, OTHER_USER)
        r = client.delete(f"/api/watchlist/{item['id']}", headers=auth(bob["access_token"]))
        assert r.status_code == 404
