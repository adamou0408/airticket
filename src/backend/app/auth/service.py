"""Authentication service — OTP generation, verification, token.

Now uses database for user storage.
"""

import hashlib
import hmac
import json
import random
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import User

OTP_TTL_SECONDS = 300
OTP_LENGTH = 6
TOKEN_TTL_SECONDS = settings.jwt_expire_minutes * 60

# OTP store — uses Redis in production, in-memory for dev
_otp_store: dict[str, str] = {}


class OtpStore:
    """In-memory OTP store. Replace with Redis in production."""
    async def set(self, phone: str, code: str):
        _otp_store[f"otp:{phone}"] = code

    async def get(self, phone: str) -> str | None:
        return _otp_store.get(f"otp:{phone}")

    async def delete(self, phone: str):
        _otp_store.pop(f"otp:{phone}", None)


otp_store = OtpStore()


async def generate_otp(phone: str) -> str:
    code = "".join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])
    await otp_store.set(phone, code)
    return code


async def verify_otp(phone: str, code: str) -> bool:
    stored = await otp_store.get(phone)
    if stored and stored == code:
        await otp_store.delete(phone)
        return True
    return False


async def get_or_create_user(db: AsyncSession, phone: str) -> tuple[User, bool]:
    """Get existing user or create new one."""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if user:
        return user, False
    user = User(phone=phone, name="")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_name(db: AsyncSession, user_id: int, name: str) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.name = name
    await db.commit()
    await db.refresh(user)
    return user


def _sign(data: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), data.encode(), hashlib.sha256).hexdigest()


def create_access_token(user_id: int) -> str:
    import base64
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS})
    sig = _sign(payload)
    return base64.urlsafe_b64encode(payload.encode()).decode() + "." + sig


def decode_access_token(token: str) -> int | None:
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
