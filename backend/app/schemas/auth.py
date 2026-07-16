"""认证相关 Pydantic v2 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    role: UserRole = UserRole.student


class LoginRequest(BaseModel):
    # 支持用户名或邮箱登录
    account: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    """PUT /users/me：昵称/头像/改密（全部可选，只更新传入字段）。"""
    nickname: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    current_password: str | None = Field(default=None, min_length=6, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: UserRole
    nickname: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
