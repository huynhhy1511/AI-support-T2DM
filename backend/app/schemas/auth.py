from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import EmailPattern, UserResponse


class RegisterRequest(BaseModel):
    email: EmailPattern
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    consent_accepted: bool = False


class LoginRequest(BaseModel):
    email: EmailPattern
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
