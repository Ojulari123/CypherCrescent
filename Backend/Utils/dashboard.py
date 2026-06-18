from decimal import Decimal

ZERO = Decimal("0")


def to_decimal(value):
    if value is None:
        return None
    return Decimal(str(value))

# Combine one Holding row with its CoinGecko market data
def enrich_holding(holding, market_by_id):
    market = market_by_id.get(holding.coin_slug, {})
    cost_basis = holding.buy_price * holding.quantity
    current_price = to_decimal(market.get("current_price"))

    if current_price is not None:
        value = current_price * holding.quantity
        pl = value - cost_basis
        pl_percent = ((current_price - holding.buy_price) / holding.buy_price) * 100 if holding.buy_price else None
    else:
        value = None
        pl = None
        pl_percent = None

    symbol = market.get("symbol")

    return {
        "id": holding.id,
        "coin_slug": holding.coin_slug,
        "quantity": holding.quantity,
        "buy_price": holding.buy_price,
        "name": market.get("name"),
        "symbol": symbol.upper() if symbol else None,
        "image": market.get("image"),
        "current_price": current_price,
        "market_cap": to_decimal(market.get("market_cap")),
        "price_change_percentage_24h": to_decimal(market.get("price_change_percentage_24h")),
        "value": value,
        "cost_basis": cost_basis,
        "pl": pl,
        "pl_percent": pl_percent,
    }

# Build the dashboard response from holdings + market data.
def build_dashboard(holdings, market_data, market_data_available=True):
    market_by_id = {m["id"]: m for m in market_data}
    enriched = [enrich_holding(h, market_by_id) for h in holdings]

    total_cost = sum((e["cost_basis"] for e in enriched), ZERO)

    with_market = [e for e in enriched if e["value"] is not None]
    if with_market:
        total_value = sum((e["value"] for e in with_market), ZERO)
        total_pl = sum((e["pl"] for e in with_market), ZERO)
        # Percent must use the cost of only the holdings we have prices for, to prevent coins without market data diluting the result
        cost_with_market = sum((e["cost_basis"] for e in with_market), ZERO)
        total_pl_percent = (total_pl / cost_with_market * 100) if cost_with_market else ZERO
    else:
        total_value = ZERO
        total_pl = ZERO
        total_pl_percent = ZERO

    performers = [e for e in enriched if e["pl_percent"] is not None]
    top = max(performers, key=lambda e: e["pl_percent"], default=None)
    worst = min(performers, key=lambda e: e["pl_percent"], default=None)

    def summary(e):
        if e is None:
            return None
        return {"coin_slug": e["coin_slug"], "name": e["name"], "pl_percent": e["pl_percent"]}

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_pl": total_pl,
        "total_pl_percent": total_pl_percent,
        "top_performer": summary(top),
        "worst_performer": summary(worst),
        "holdings": enriched,
        "market_data_available": market_data_available,
    }
