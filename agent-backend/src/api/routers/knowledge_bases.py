"""
knowledge_bases.py — 知识库管理 API 路由

接口列表:
  POST   /                创建知识库
  GET    /                获取用户的所有知识库（列表）
  GET    /{kb_id}         获取知识库详情
  DELETE /{kb_id}         删除知识库（级联删除文档 + 向量）
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.auth.security import get_current_user_id
from src.models.document import Document
from src.models.knowledge_base import KnowledgeBase
from src.schemas.knowledge_base import (
    CreateKnowledgeBaseRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)
from src.core.rag.vector_store import VectorStoreService
from src.services.file_storage import FileStorageService
from src.logger.logger import logger

router = APIRouter()
vector_store = VectorStoreService()


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    req: CreateKnowledgeBaseRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建知识库"""
    # 每个用户只允许一个知识库
    existing = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="每个用户只能创建一个知识库")

    kb = KnowledgeBase(
        user_id=user_id,
        name=req.name,
        description=req.description,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有知识库"""
    query = select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
    result = await db.execute(query)
    kbs = list(result.scalars().all())

    items = []
    for kb in kbs:
        count_query = select(func.count()).select_from(
            select(Document).where(Document.kb_id == kb.id).subquery()
        )
        doc_count = (await db.execute(count_query)).scalar() or 0
        resp = KnowledgeBaseResponse.model_validate(kb)
        resp.document_count = doc_count
        items.append(resp)

    return KnowledgeBaseListResponse(items=items, total=len(items))


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库详情"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    count_query = select(func.count()).select_from(
        select(Document).where(Document.kb_id == kb_id).subquery()
    )
    doc_count = (await db.execute(count_query)).scalar() or 0
    resp = KnowledgeBaseResponse.model_validate(kb)
    resp.document_count = doc_count
    return resp


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除知识库（级联删除所有文档 + 向量）"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 1. 查出所有文档，删除本地存储文件
    docs_result = await db.execute(select(Document).where(Document.kb_id == kb_id))
    docs = list(docs_result.scalars().all())
    file_storage = FileStorageService()
    for doc in docs:
        if doc.file_path:
            try:
                file_storage.delete(doc.file_path)
            except Exception as e:
                logger.warning(f"删除本地文件失败: id={doc.id}, path={doc.file_path}, error={e}")

    # 2. 删向量
    await vector_store.delete_by_kb_id(kb_id)
    # 3. 删文档记录
    await db.execute(delete(Document).where(Document.kb_id == kb_id))
    # 4. 删知识库
    await db.delete(kb)
    await db.commit()

    return {"status": "deleted", "message": f"知识库 {kb_id} 已删除"}