from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.logger.logger import logger

from src.db.session import get_db
from src.auth.security import security, get_current_user_id
from src.services.conversation import (
    get_conversation_with_messages,
    list_conversations,
    count_conversations,
    update_conversation,
    delete_conversation,
)

router = APIRouter()


class UpdateConversationBody(BaseModel):
    """修改会话请求体"""
    title: str | None = Field(None, description="新标题")


# ──────────────────────────────────────────────
# 会话列表（分页）
# ──────────────────────────────────────────────
@router.get("")
async def list_convs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = Query(50, ge=1, le=200, description="每页条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表（按更新时间倒序）"""
    user_id = await get_current_user_id(credentials)
    logger.info(f"【会话】获取会话列表 | user={user_id} limit={limit} offset={offset}")
    convs = await list_conversations(db, user_id, limit=limit, offset=offset)
    total = await count_conversations(db, user_id)
    return {"data": convs, "total": total}


# ──────────────────────────────────────────────
# 会话详情（含全部消息）
# ──────────────────────────────────────────────
@router.get("/{session_id}")
async def get_conv(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情（含全部消息），校验归属"""
    user_id = await get_current_user_id(credentials)
    logger.info(f"【会话】获取会话详情 | session={session_id} user={user_id}")
    data = await get_conversation_with_messages(db, session_id, user_id=user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return data


# ──────────────────────────────────────────────
# 修改会话
# ──────────────────────────────────────────────
@router.put("/{session_id}")
async def update_conv(
    session_id: str,
    body: UpdateConversationBody,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """修改会话标题，校验归属"""
    user_id = await get_current_user_id(credentials)
    logger.info(f"【会话】修改会话标题 | session={session_id} user={user_id} title={body.title}")
    updated = await update_conversation(db, session_id, title=body.title, user_id=user_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return updated


# ──────────────────────────────────────────────
# 删除会话（级联删除所有消息）
# ──────────────────────────────────────────────
@router.delete("/{session_id}", status_code=204)
async def delete_conv(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（级联删除所有消息），校验归属"""
    user_id = await get_current_user_id(credentials)
    logger.info(f"【会话】删除会话 | session={session_id} user={user_id}")
    success = await delete_conversation(db, session_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return Response(status_code=204)
