import json
import logging
from typing import Any, Callable, Optional
import redis
import redis.exceptions as redis_exc
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from Config.config import settings

logger = logging.getLogger(__name__)

try:
    # Upstash drops idle connections, so a pooled connection can be dead by the next request. 
    # health_check_interval revalidates before use, and retry/retry_on_error transparently reconnects on a dropped
    # connection ("Connection closed by server") instead of surfacing a 500.
    redis_client: Optional[redis.Redis] = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        socket_keepalive=True,
        health_check_interval=30,
        retry=Retry(ExponentialBackoff(cap=1.0, base=0.1), 3),
        retry_on_error=[redis_exc.ConnectionError, redis_exc.TimeoutError],
    )
except Exception as e:
    logger.warning("Failed to create Redis client (%s). Cache will be a no-op.", e)
    redis_client = None

# Return cached JSON value if present; otherwise call fetch_fn and store its result for ttl seconds
def cached(key: str, ttl: int, fetch_fn: Callable[[], Any]) -> Any:
    if redis_client is not None:
        try:
            hit = redis_client.get(key)
            if hit is not None:
                return json.loads(hit)
        except Exception as e:
            logger.warning("Redis GET failed for %s: %s", key, e)

    value = fetch_fn()

    if redis_client is not None:
        try:
            redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning("Redis SETEX failed for %s: %s", key, e)

    return value
