from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class PinLoginRequest(BaseModel):
    phone_number: str
    pin: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
