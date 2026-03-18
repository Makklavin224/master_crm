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
