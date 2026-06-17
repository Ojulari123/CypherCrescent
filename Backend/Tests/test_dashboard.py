import httpx
from decimal import Decimal
from unittest.mock import patch
from conftest import auth, register

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
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "image": "https://example.com/eth.png",
        "current_price": 4000,
        "market_cap": 420_000_000_000,
        "price_change_percentage_24h": -1.20,
    },
]


def add_holding(client, token, coin_slug, quantity, buy_price):
    r = client.post(
        "/api/holdings",
        json={"coin_slug": coin_slug, "quantity": str(quantity), "buy_price": str(buy_price)},
        headers=auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# /api/dashboard
class TestDashboard:
    def test_empty_portfolio(self, client):
        body = register(client)
        r = client.get("/api/dashboard", headers=auth(body["access_token"]))
        assert r.status_code == 200
        data = r.json()
        assert Decimal(data["total_value"]) == 0
        assert Decimal(data["total_cost"]) == 0
        assert Decimal(data["total_pl"]) == 0
        assert data["top_performer"] is None
        assert data["worst_performer"] is None
        assert data["holdings"] == []
        assert data["market_data_available"] is True

    def test_computes_value_pl_and_performers(self, client):
        body = register(client)
        # BTC: bought 0.5 @ 60000 (cost 30000), now 70000 → value 35000, pl 5000, pl% +16.67
        # ETH: bought 2 @ 5000 (cost 10000), now 4000 → value 8000, pl -2000, pl% -20
        add_holding(client, body["access_token"], "bitcoin", "0.5", "60000")
        add_holding(client, body["access_token"], "ethereum", "2", "5000")

        with patch("Routes.dashboard.get_markets", return_value=SAMPLE_MARKETS):
            r = client.get("/api/dashboard", headers=auth(body["access_token"]))

        assert r.status_code == 200
        data = r.json()

        assert Decimal(data["total_value"]) == Decimal("43000")
        assert Decimal(data["total_cost"]) == Decimal("40000")
        assert Decimal(data["total_pl"]) == Decimal("3000")
        # 3000 / 40000 * 100 = 7.5
        assert Decimal(data["total_pl_percent"]).quantize(Decimal("0.01")) == Decimal("7.50")

        assert data["top_performer"]["coin_slug"] == "bitcoin"
        assert data["worst_performer"]["coin_slug"] == "ethereum"

        by_slug = {h["coin_slug"]: h for h in data["holdings"]}
        btc = by_slug["bitcoin"]
        assert btc["name"] == "Bitcoin"
        assert btc["symbol"] == "BTC"
        assert Decimal(btc["value"]) == Decimal("35000")
        assert Decimal(btc["pl"]) == Decimal("5000")

    def test_degrades_when_coingecko_down(self, client):
        body = register(client)
        add_holding(client, body["access_token"], "bitcoin", "0.5", "60000")

        with patch("Routes.dashboard.get_markets", side_effect=httpx.HTTPError("down")):
            r = client.get("/api/dashboard", headers=auth(body["access_token"]))

        assert r.status_code == 200
        data = r.json()
        assert data["market_data_available"] is False
        assert Decimal(data["total_cost"]) == Decimal("30000")
        assert Decimal(data["total_value"]) == Decimal("0")
        assert Decimal(data["total_pl"]) == Decimal("0")
        assert data["holdings"][0]["current_price"] is None
        assert data["holdings"][0]["value"] is None
        assert data["top_performer"] is None
        assert data["worst_performer"] is None

    def test_unknown_coin_slug_returns_null_market_fields(self, client):
        body = register(client)
        add_holding(client, body["access_token"], "shitcoin69", "100", "1")

        with patch("Routes.dashboard.get_markets", return_value=[]):
            r = client.get("/api/dashboard", headers=auth(body["access_token"]))

        assert r.status_code == 200
        data = r.json()
        h = data["holdings"][0]
        assert h["coin_slug"] == "shitcoin69"
        assert h["current_price"] is None
        assert h["name"] is None
        assert Decimal(h["cost_basis"]) == Decimal("100")
        assert data["top_performer"] is None

    def test_unauthenticated_401(self, client):
        r = client.get("/api/dashboard")
        assert r.status_code == 401
