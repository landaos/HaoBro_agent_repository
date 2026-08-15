"""
documents.py — 文档管理 API 路由

所有路由挂载在 /api/v1/knowledge-bases/{kb_id}/documents 下

接口列表:
  POST   /upload             上传单个文档
  POST   /batch-upload       批量上传文档（最多 10 个）
  GET    /                   文档列表（分页）
  GET    /{doc_id}           文档详情
  DELETE /{doc_id}           删除单个文档
  POST   /batch-delete       批量删除文档
  POST   /{doc_id}/reprocess 重新处理文档
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.auth.security import get_current_user_id
from src.models.knowledge_base import KnowledgeBase
from src.schemas.common import PaginatedResponse
from src.schemas.document import (
    BatchDeleteRequest,
    BatchUploadResponse,
    DeleteResponse,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from src.services.document_service import DocumentService, process_doc_in_background

router = APIRouter()
doc_service = DocumentService()


async def _check_kb_ownership(kb_id: int, user_id: str, db: AsyncSession):
    """校验知识库是否属于当前用户"""
    from sqlalchemy import select
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.post("/{kb_id}/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文档到知识库。

    支持 PDF / TXT / MD 格式，文件最大 50MB。
    上传后自动执行: 文档加载 → 智能分块 → 向量化 → 入库（后台异步执行）。
    """
    await _check_kb_ownership(kb_id, user_id, db)

    file_data = await file.read()

    try:
        doc = await doc_service.create_record(
            db=db,
            kb_id=kb_id,
            file_data=file_data,
            file_name=file.filename or "untitled",
            title=title,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 后台处理（独立 session）
    absolute_path = doc_service.file_storage.get_absolute_path(doc.file_path)
    asyncio.create_task(
        process_doc_in_background(
            file_path=absolute_path,
            kb_id=kb_id,
            doc_id=doc.id,
            user_id=user_id,
        )
    )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(doc),
    )


@router.post("/{kb_id}/documents/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_documents(
    kb_id: int,
    files: list[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    批量上传文档（最多 10 个文件）。
    """
    await _check_kb_ownership(kb_id, user_id, db)

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="一次最多上传 10 个文件")

    documents = []
    errors = []

    for file in files:
        try:
            file_data = await file.read()
            doc = await doc_service.create_record(
                db=db,
                kb_id=kb_id,
                file_data=file_data,
                file_name=file.filename or "untitled",
            )

            absolute_path = doc_service.file_storage.get_absolute_path(doc.file_path)
            asyncio.create_task(
                process_doc_in_background(
                    file_path=absolute_path,
                    kb_id=kb_id,
                    doc_id=doc.id,
                    user_id=user_id,
                )
            )

            documents.append(DocumentResponse.model_validate(doc))
        except ValueError as e:
            errors.append({"filename": file.filename, "error": str(e)})
        except Exception as e:
            errors.append({"filename": file.filename, "error": f"未知错误: {e}"})

    return BatchUploadResponse(
        documents=documents,
        failed_count=len(errors),
        errors=errors,
    )


@router.get("/{kb_id}/documents", response_model=PaginatedResponse[DocumentResponse])
async def list_documents(
    kb_id: int,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    file_type: str | None = None,
    search: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库下的文档列表（分页）"""
    await _check_kb_ownership(kb_id, user_id, db)

    docs, total = await doc_service.get_list(
        db=db,
        kb_id=kb_id,
        page=page,
        page_size=page_size,
        status=status,
        file_type=file_type,
        search=search,
    )
    return PaginatedResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(
    kb_id: int,
    doc_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取文档详情"""
    await _check_kb_ownership(kb_id, user_id, db)

    doc = await doc_service.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return DocumentDetailResponse.model_validate(doc)


@router.delete("/{kb_id}/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    kb_id: int,
    doc_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除文档（同步清理向量数据 + 存储文件）"""
    await _check_kb_ownership(kb_id, user_id, db)

    try:
        result = await doc_service.delete(db=db, doc_id=doc_id)
        return DeleteResponse(
            status="deleted",
            deleted_vector_count=result.get("deleted_vector_count", 0),
            message=f"文档 {doc_id} 已删除",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{kb_id}/documents/batch-delete", response_model=DeleteResponse)
async def batch_delete_documents(
    kb_id: int,
    req: BatchDeleteRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """批量删除文档"""
    await _check_kb_ownership(kb_id, user_id, db)

    deleted_count = await doc_service.batch_delete(db=db, doc_ids=req.doc_ids)
    return DeleteResponse(
        status="deleted",
        message=f"成功删除 {deleted_count}/{len(req.doc_ids)} 个文档",
    )


@router.post("/{kb_id}/documents/{doc_id}/reprocess", response_model=DocumentUploadResponse)
async def reprocess_document(
    kb_id: int,
    doc_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """重新处理文档"""
    await _check_kb_ownership(kb_id, user_id, db)

    doc = await doc_service.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    await doc_service.vector_store.delete_by_doc_id(doc_id)

    absolute_path = doc_service.file_storage.get_absolute_path(doc.file_path) if doc.file_path else ""
    doc.status = "processing"
    doc.chunk_count = 0
    await db.commit()

    asyncio.create_task(
        process_doc_in_background(
            file_path=absolute_path,
            kb_id=kb_id,
            doc_id=doc_id,
            user_id=user_id,
        )
    )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(doc),
        message="重新处理中",
    )