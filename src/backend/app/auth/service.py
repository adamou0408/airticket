"""Authentication service — OTP generation, verification, token.

Spec: specs/travel-planner-app/spec.md — US-3, US-5
Task: 2.1 — User authentication service

Flow:
1. User sends phone number → we generate 6-digit OTP, store in Redis (5 min TTL)
2. User sends phone + OTP → we verify, create user if new, return token
"""

import hashlib
import hmac
import json
import random
import time

from app.core.config import settings

OTP_TTL_SECONDS = 300  # 5 minutes
OTP_LENGTH = 6
TOKEN_TTL_SECONDS = settings.jwt_expire_minutes * 60


async def generate_otp(phone: str, redis_client) -> str:
    """Generate and store a 6-digit OTP for the given phone number."""
    code = "".join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])
    key = f"otp:{phone}"
    await redis_client.setex(key, OTP_TTL_SECONDS, code)
    return code


async def verify_otp(phone: str, code: str, redis_client) -> bool:
    """Verify OTP against stored value in Redis."""
    key = f"otp:{phone}"
    stored = await redis_client.get(key)
    if stored and stored == code:
        await redis_client.delete(key)  # One-time use
        return True
    return False


def _sign(data: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), data.encode(), hashlib.sha256).hexdigest()


def create_access_token(user_id: int) -> str:
    """Create a signed access token (HMAC-based)."""
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS})
    sig = _sign(payload)
    import base64
    token = base64.urlsafe_b64encode(payload.encode()).decode() + "." + sig
    return token


def decode_access_token(token: str) -> int | None:
    """Decode token and return user_id, or None if invalid/expired."""
    try:
        import base64
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        payload_str = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        if _sign(payload_str) != sig:
            return None
        payload = json.loads(payload_str)
        if payload.get("exp", 0) < time.time():
            return None
        return int(payload["sub"])
    except Exception:
        return None
