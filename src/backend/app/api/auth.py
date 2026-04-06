"""Auth API endpoints — database-backed."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id
from app.auth.schemas import (
    SendCodeRequest, SendCodeResponse,
    TokenResponse, UpdateProfileRequest, UserProfile, VerifyCodeRequest,
)
from app.auth.service import (
    create_access_token, generate_otp, get_or_create_user,
    get_user_by_id, update_user_name, verify_otp,
)
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(request: SendCodeRequest):
    code = await generate_otp(request.phone)
    print(f"[DEV] OTP for {request.phone}: {code}")
    return SendCodeResponse()


@router.post("/verify", response_model=TokenResponse)
async def verify_code(request: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    valid = await verify_otp(request.phone, request.code)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="驗證碼錯誤或已過期")

    user, is_new = await get_or_create_user(db, request.phone)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id, is_new_user=is_new)


@router.get("/me", response_model=UserProfile)
async def get_profile(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return UserProfile.model_validate(user)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user_name(db, user_id, request.name)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return UserProfile.model_validate(user)
