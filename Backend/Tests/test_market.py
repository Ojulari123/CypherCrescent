import httpx
from unittest.mock import patch
from conftest import auth, register

SAMPLE_MARKETS = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "image": "https://example.com/btc.png",
        "current_price": 67432.10,
        "market_cap": 1_300_000_000_000,
        "price_change_percentage_24h": 2.34,
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "image": "https://example.com/eth.png",
        "current_price": 3500.50,
        "market_cap": 420_000_000_000,
        "price_change_percentage_24h": -1.20,
    },
]

SAMPLE_SEARCH = [
    {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc", "thumb": "https://t/btc.png", "large": "https://l/btc.png", "market_cap_rank": 1},
    {"id": "bitcoin-cash", "name": "Bitcoin Cash", "symbol": "bch", "thumb": "https://t/bch.png", "large": "https://l/bch.png", "market_cap_rank": 21},
]


# /api/market/coins
class TestMarketCoins:
    def test_returns_market_data(self, client):
        body = register(client)
        with patch("Routes.market.get_markets", return_value=SAMPLE_MARKETS):
            r = client.get("/api/market/coins?ids=bitcoin,ethereum", headers=auth(body["access_token"]))
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["name"] == "Bitcoin"
        assert data[1]["symbol"] == "eth"

    def test_empty_ids_400(self, client):
        body = register(client)
        r = client.get("/api/market/coins?ids=,", headers=auth(body["access_token"]))
        assert r.status_code == 400

    def test_coingecko_down_returns_502(self, client):
        body = register(client)
        with patch("Routes.market.get_markets", side_effect=httpx.HTTPError("down")):
            r = client.get("/api/market/coins?ids=bitcoin", headers=auth(body["access_token"]))
        assert r.status_code == 502

    def test_unauthenticated_401(self, client):
        r = client.get("/api/market/coins?ids=bitcoin")
        assert r.status_code == 401


# /api/market/search
class TestMarketSearch:
    def test_returns_results(self, client):
        body = register(client)
        with patch("Routes.market.search_coins", return_value=SAMPLE_SEARCH):
            r = client.get("/api/market/search?q=bitcoin", headers=auth(body["access_token"]))
        assert r.status_code == 200
        assert len(r.json()) == 2
        assert r.json()[0]["id"] == "bitcoin"

    def test_empty_query_422(self, client):
        body = register(client)
        r = client.get("/api/market/search?q=", headers=auth(body["access_token"]))
        assert r.status_code == 422

    def test_coingecko_down_returns_502(self, client):
        body = register(client)
        with patch("Routes.market.search_coins", side_effect=httpx.HTTPError("down")):
            r = client.get("/api/market/search?q=bitcoin", headers=auth(body["access_token"]))
        assert r.status_code == 502

    def test_unauthenticated_401(self, client):
        r = client.get("/api/market/search?q=bitcoin")
        assert r.status_code == 401
