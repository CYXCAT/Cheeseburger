"""认证请求/响应模型。"""
from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    invite_token: str = Field(..., min_length=1, max_length=64)
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False

    class Config:
        from_attributes = True
