from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TgAuthRequest(BaseModel):
    init_data: str


class MaxAuthRequest(BaseModel):
    init_data: str  # MAX initData (same format as TG)


class VkAuthRequest(BaseModel):
    launch_params: str  # VK launch params query string (contains vk_user_id, sign, etc.)


class QrInitResponse(BaseModel):
    session_id: str
    qr_payload: str


class QrStatusResponse(BaseModel):
    status: str
    access_token: str | None = None


class QrConfirmRequest(BaseModel):
    session_id: str
    tg_user_id: str


class MagicLinkVerifyRequest(BaseModel):
    token: str
