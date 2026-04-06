from pydantic import BaseModel, EmailStr


class LoginSchemaBase(BaseModel):
    email: EmailStr
    password: str


class Login(LoginSchemaBase):
    pass


class RefreshTokenRequest(BaseModel):
    """Request body for /auth/refresh endpoint."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response for both /auth/login and /auth/refresh endpoints."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
