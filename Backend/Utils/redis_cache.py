import json
import logging
from typing import Any, Callable, Optional

import redis

from Config.config import settings

logger = logging.getLogger(__name__)

try:
    redis_client: Optional[redis.Redis] = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
except Exception as e:
    logger.warning("Failed to create Redis client (%s). Cache will be a no-op.", e)
    redis_client = None


def cached(key: str, ttl: int, fetch_fn: Callable[[], Any]) -> Any:
    """Return cached JSON value if present; otherwise call fetch_fn and store its result for ttl seconds."""
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
