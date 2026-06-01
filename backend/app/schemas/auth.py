from uuid import UUID

from pydantic import BaseModel, Field


class OtpSendRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    country_code: str = "IN"


class OtpSendResponse(BaseModel):
    request_id: UUID


class OtpVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in_seconds: int
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class CustomerMeResponse(BaseModel):
    id: UUID
    phone: str | None
    email: str | None
    status: str


class SignupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class SigninRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
