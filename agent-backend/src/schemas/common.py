"""通用 Pydantic Schema"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """统一错误响应"""

    error_code: str
    message: str
    detail: Any | None = None
    request_id: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应"""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    version: str
    timestamp: str
    checks: dict[str, str] = {}
