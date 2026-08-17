# ============================================
# user.py - 用户相关 Pydantic Schema
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的 Schema：
# ═══════════════════════════════════════════
#
# 1. CreateUserRequest
#    username: str          # 用户名，3-64 位，字母数字下划线
#    display_name: str      # 显示名，可空
#    email: EmailStr        # 邮箱，可空
#    phone: str             # 手机号，可空
#    password: str          # 密码，8-128 位
#    role_id: int           # 角色 ID，可空（默认 viewer）
#
# 2. UpdateUserRequest
#    display_name: str | None
#    email: EmailStr | None
#    phone: str | None
#
# 3. ChangeRoleRequest
#    role_id: int
#
# 4. SetActiveRequest
#    is_active: bool
#
# 5. ChangePasswordRequest
#    old_password: str
#    new_password: str      # 密码强度校验
#
# 6. LoginRequest
#    username: str
#    password: str
#
# 7. TokenResponse
#    access_token: str
#    token_type: str = "bearer"
#    expires_in: int
#
# 8. UserResponse
#    id: int
#    username: str
#    display_name: str | None
#    email: str | None
#    phone: str | None
#    role_id: int | None
#    role_name: str | None
#    is_active: bool
#    is_superuser: bool
#    last_login_at: datetime | None
#    created_at: datetime
#    permissions: list[str]     # 该用户拥有的所有权限代码
#
# ═══════════════════════════════════════════
# 密码强度校验（使用 Pydantic field_validator）：
# ═══════════════════════════════════════════
#
#   @field_validator("password")
#   @classmethod
#   def validate_password(cls, v):
#       if len(v) < 8:
#           raise ValueError("密码至少 8 位")
#       if not re.search(r"[a-zA-Z]", v):
#           raise ValueError("密码需包含字母")
#       if not re.search(r"\d", v):
#           raise ValueError("密码需包含数字")
#       if v in COMMON_PASSWORDS:
#           raise ValueError("密码过于常见，请更换")
#       return v
# ═══════════════════════════════════════════

import re

from pydantic import BaseModel, Field, EmailStr, field_validator


def _validate_password_strength(v: str) -> str:
    """密码强度校验：至少包含一个字母和一个数字"""
    if not re.search(r"[a-zA-Z]", v):
        raise ValueError("密码必须包含至少一个字母")
    if not re.search(r"\d", v):
        raise ValueError("密码必须包含至少一个数字")
    return v


class LoginRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str = Field(..., min_length=6, max_length=20)


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)
    confirm_password: str = Field(..., min_length=6, max_length=20)
    phone: str | None = None
    gender: int | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class ResetPasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=20)
    new_password: str = Field(..., min_length=6, max_length=20)
    confirm_password: str = Field(..., min_length=6, max_length=20)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserUpdateRequest(BaseModel):
    username: str | None = None
    phone: str | None = None
    gender: int | None = None


class TokenRefreshRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    user_id: str | None = None
    username: str
    email: str
    phone: str | None = None
    gender: int | None = None
    status: int | None = None


class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    token: str


class RegisterResponse(BaseModel):
    status: int
    message: str
    user: UserResponse
    token: str


class ActionResponse(BaseModel):
    message: str
    user: UserResponse | None = None
    token: str | None = None


class UserDetailResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse



