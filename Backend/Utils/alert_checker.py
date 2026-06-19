import logging
from datetime import datetime, timezone
from tables import Local_Session, PriceAlert
from Utils.coingecko import get_markets, MarketDataError
from Utils.email import send_price_alert_email

logger = logging.getLogger(__name__)

def check_price_alerts() -> None:
    db = Local_Session()
    try:
        alerts = db.query(PriceAlert).filter(PriceAlert.triggered == False).all()
        if not alerts:
            return

        slugs = list({a.coin_slug for a in alerts})
        try:
            market_data = get_markets(slugs)
        except MarketDataError:
            logger.warning("Alert checker: could not fetch market data, skipping run")
            return

        price_map = {c["id"]: float(c["current_price"]) for c in market_data if c.get("current_price") is not None}
        name_map = {c["id"]: c.get("name", c["id"]) for c in market_data}

        now = datetime.now(timezone.utc)
        for alert in alerts:
            current_price = price_map.get(alert.coin_slug)
            if current_price is None:
                continue

            target = float(alert.target_price)
            triggered = ((alert.direction == "above" and current_price >= target) or (alert.direction == "below" and current_price <= target))

            if triggered:
                alert.triggered = True
                alert.triggered_at = now
                try:
                    send_price_alert_email(
                        to_email=alert.user.email,
                        first_name=alert.user.first_name,
                        coin_name=name_map.get(alert.coin_slug, alert.coin_slug),
                        coin_slug=alert.coin_slug,
                        direction=alert.direction,
                        target_price=target,
                        current_price=current_price,
                    )
                except Exception:
                    logger.exception("Failed to send price alert email for alert %s", alert.id)

        db.commit()
        logger.info("Alert checker complete — checked %d alerts for %d coins", len(alerts), len(slugs))
    except Exception:
        logger.exception("Alert checker unexpected error")
        db.rollback()
    finally:
        db.close()
