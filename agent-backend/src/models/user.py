import uuid
import enum

from sqlalchemy import Integer, String, Index
from sqlalchemy.orm import mapped_column, Mapped

from src.models.base import Base, TimeMixin


class Gender(enum.IntEnum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class UserStatusChoice:
    LOCKED = 2
    ACTIVE = 1
    DISABLED = 0


class User(Base, TimeMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
    )
    user_name: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="用户名",
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="邮箱",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="手机号",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希值",
    )
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=UserStatusChoice.ACTIVE, comment="用户状态",
    )
    gender: Mapped[int] = mapped_column(
        Integer, nullable=False, default=Gender.UNKNOWN, comment="性别: 0=未知, 1=男, 2=女",
    )

    __table_args__ = (
        Index("idx_users_user_name", "user_name"),
    )