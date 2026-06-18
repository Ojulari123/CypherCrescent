import secrets
from fastapi import HTTPException, status
from Utils.redis_cache import redis_client
from Config.config import settings
from Utils.security import create_refresh_token

def require_redis():
    if redis_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Session service is temporarily unavailable")

def session_key(user_id: int, sid: str) -> str:
    return f"refresh:{user_id}:{sid}"

def session_ttl() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

# Start a new refresh session and return a refresh token for it
def issue_refresh_token(user_id: int, token_version: int) -> str:
    require_redis()
    sid = secrets.token_urlsafe(16)
    jti = secrets.token_urlsafe(16)
    redis_client.setex(session_key(user_id, sid), session_ttl(), jti)
    return create_refresh_token(user_id, token_version, sid, jti)

# Rotate a refresh session: the presented jti must be the current one. On a match
# we issue a fresh token; on reuse of an already-rotated jti we revoke the whole
# session (likely theft). Returns a new refresh token.
def rotate_refresh_token(user_id: int, token_version: int, sid: str, jti: str) -> str:
    require_redis()
    key = session_key(user_id, sid)
    current = redis_client.get(key)

    if current is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is no longer valid. Please log in again.")

    if current != jti:
        redis_client.delete(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected. This session has been revoked, please log in again.")

    new_jti = secrets.token_urlsafe(16)
    redis_client.setex(key, session_ttl(), new_jti)
    return create_refresh_token(user_id, token_version, sid, new_jti)
