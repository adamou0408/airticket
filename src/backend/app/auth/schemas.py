"""Pydantic schemas for auth API.

Task: 2.1 — User authentication service
"""

from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    phone: str = Field(..., description="Phone number with country code", examples=["+886912345678"])


class SendCodeResponse(BaseModel):
    message: str = "驗證碼已發送"
    expires_in_seconds: int = 300


class VerifyCodeRequest(BaseModel):
    phone: str = Field(..., examples=["+886912345678"])
    code: str = Field(..., min_length=6, max_length=6, examples=["123456"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_new_user: bool = False


class UserProfile(BaseModel):
    id: int
    phone: str
    name: str

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
