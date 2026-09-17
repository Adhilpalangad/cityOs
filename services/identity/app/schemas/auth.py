from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.common import validate_password_strength


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    _validate_password = field_validator("password")(validate_password_strength)


class RegisterResponse(BaseModel):
    id: str
    email: str
    status: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    _validate_password = field_validator("new_password")(validate_password_strength)


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: str | None
    permissions: list[str]
    email_verified: bool
    status: str
