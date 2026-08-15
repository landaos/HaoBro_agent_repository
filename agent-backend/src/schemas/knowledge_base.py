"""知识库相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""

    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: str | None = Field(None, description="描述")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""

    id: int
    user_id: str
    name: str
    description: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""

    items: list[KnowledgeBaseResponse]
    total: int
