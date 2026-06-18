import json
import secrets
from fastapi import HTTPException, status
from Utils.redis_cache import redis_client
from Config.config import settings

MAX_ATTEMPTS = 5

def otp_key(user_id: int, purpose: str) -> str:
    return f"2fa:{purpose}:{user_id}"

def require_redis():
    if redis_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Two-factor service is temporarily unavailable")

# Generate a 6-digit code, store it with a TTL, and return it to be emailed
def create_code(user_id: int, purpose: str) -> str:
    require_redis()
    code = f"{secrets.randbelow(1_000_000):06d}"
    ttl = settings.OTP_EXPIRE_MINUTES * 60
    redis_client.setex(otp_key(user_id, purpose), ttl, json.dumps({"code": code, "attempts": 0}))
    return code

# Check a submitted code; accept it on success, and drop it after too many wrong attempts
def verify_code(user_id: int, purpose: str, code: str) -> bool:
    require_redis()
    key = otp_key(user_id, purpose)
    raw = redis_client.get(key)
    if raw is None:
        return False

    data = json.loads(raw)
    if data["code"] == code:
        redis_client.delete(key)
        return True

    attempts = data.get("attempts", 0) + 1
    if attempts >= MAX_ATTEMPTS:
        redis_client.delete(key)
    else:
        ttl = redis_client.ttl(key)
        if ttl and ttl > 0:
            redis_client.setex(key, ttl, json.dumps({"code": data["code"], "attempts": attempts}))
    return False
