"""文档相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """文档响应"""

    id: int
    kb_id: int
    title: str
    file_name: str
    file_type: str
    file_size: int | None = None
    chunk_count: int = 0
    status: str = "pending"
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    """文档详情响应"""

    pass


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""

    document: DocumentResponse
    message: str = "上传成功，正在处理中"


class BatchUploadResponse(BaseModel):
    """批量上传响应"""

    documents: list[DocumentResponse]
    failed_count: int = 0
    errors: list[dict] = []


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    doc_ids: list[int] = Field(..., min_length=1, max_length=100)


class DeleteResponse(BaseModel):
    """删除响应"""

    status: str = "deleted"
    deleted_vector_count: int = 0
    message: str = ""
