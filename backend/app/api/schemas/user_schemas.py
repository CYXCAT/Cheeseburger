"""用户设置请求模型。"""
from pydantic import BaseModel, Field


class UserUpdateIn(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=64)
    password: str | None = Field(None, min_length=6, max_length=128)
