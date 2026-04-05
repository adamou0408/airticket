"""Auth API endpoints.

Spec: specs/travel-planner-app/spec.md — US-3, US-5
Task: 2.1 — User authentication service
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user_id
from app.auth.schemas import (
    SendCodeRequest,
    SendCodeResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
    VerifyCodeRequest,
)
from app.auth.service import create_access_token, generate_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory user store for MVP (will be replaced with DB in production)
_users: dict[str, dict] = {}  # phone -> {id, phone, name}
_next_id = 1


def _get_or_create_user(phone: str) -> tuple[dict, bool]:
    """Get existing user or create new one. Returns (user, is_new)."""
    global _next_id
    if phone in _users:
        return _users[phone], False
    user = {"id": _next_id, "phone": phone, "name": ""}
    _users[phone] = user
    _next_id += 1
    return user, True


def _get_user_by_id(user_id: int) -> dict | None:
    for u in _users.values():
        if u["id"] == user_id:
            return u
    return None


# Shared fake Redis for testing (when real Redis isn't available)
_otp_store: dict[str, str] = {}


class FakeRedis:
    """In-memory Redis substitute for testing/dev."""
    async def setex(self, key, ttl, value):
        _otp_store[key] = value

    async def get(self, key):
        return _otp_store.get(key)

    async def delete(self, key):
        _otp_store.pop(key, None)


_fake_redis = FakeRedis()


@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(request: SendCodeRequest):
    """Send a 6-digit verification code to the phone number."""
    code = await generate_otp(request.phone, _fake_redis)
    # In production: send via Twilio SMS
    # For dev: log the code
    print(f"[DEV] OTP for {request.phone}: {code}")
    return SendCodeResponse()


@router.post("/verify", response_model=TokenResponse)
async def verify_code(request: VerifyCodeRequest):
    """Verify OTP and return JWT token. Auto-registers new users."""
    valid = await verify_otp(request.phone, request.code, _fake_redis)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="驗證碼錯誤或已過期")

    user, is_new = _get_or_create_user(request.phone)
    token = create_access_token(user["id"])

    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        is_new_user=is_new,
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(user_id: int = Depends(get_current_user_id)):
    """Get current user profile."""
    user = _get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return UserProfile(**user)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Update current user profile."""
    user = _get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    user["name"] = request.name
    return UserProfile(**user)
