import asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain.chat_models import init_chat_model
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate

from src.logger.logger import logger

from src.config import settings
from src.models import Conversation, Message


def _message_to_dict(msg: Message) -> dict:
    """将 Message ORM 对象转为前端可直接消费的 dict"""
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "content": msg.content,
        "extra_data": msg.extra_data,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _conversation_to_dict(conv: Conversation) -> dict:
    """将 Conversation ORM 对象转为前端可直接消费的 dict"""
    return {
        "id": conv.id,
        "session_id": conv.session_id,
        "user_id": conv.user_id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


# ── 会话标题生成链（懒加载，只在首次调用时初始化） ──
_title_chain = None


def _get_title_chain():
    global _title_chain
    if _title_chain is None:
        llm = ChatTongyi(
            model_name=settings.chat_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            streaming=True,
            top_p=0.3,
        )
        prompt = ChatPromptTemplate.from_template(
            "请根据用户输入生成一个简短的会话标题（10 字左右），概括核心内容。\n用户输入：{input}"
        )
        _title_chain = prompt | llm
    return _title_chain


async def create_conversation(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    user_input: str,
) -> dict:
    """
    创建新会话，并根据用户第一条消息自动生成标题。

    如果 AI 标题生成失败（API 限流、网络异常等），使用用户输入的前 20 字作为后备标题，
    确保会话总能被保存，不阻塞前端流程。
    """
    title = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            chain = _get_title_chain()
            response = await chain.ainvoke({"input": user_input})
            title = response.content.strip()
            break
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"【会话】标题生成失败(第{attempt}次重试)，等待 {2*attempt}s 后重试 | {e}")
                await asyncio.sleep(2 * attempt)
            else:
                logger.warning(f"【会话】标题生成失败(重试{max_retries}次均失败)，使用后备标题 | {e}")
    if not title:
        title = (user_input or "新会话")[:20]

    conversation = Conversation(
        session_id=session_id,
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return _conversation_to_dict(conversation)


async def get_conversation(
    db: AsyncSession,
    session_id: str,
    user_id: str | None = None,
) -> dict | None:
    """按 session_id 查询会话，可选 user_id 校验归属"""
    where = [Conversation.session_id == session_id]
    if user_id is not None:
        where.append(Conversation.user_id == user_id)
    result = await db.execute(
        select(Conversation).where(*where)
    )
    conv = result.scalars().first()
    return _conversation_to_dict(conv) if conv else None


async def get_conversation_with_messages(
    db: AsyncSession,
    session_id: str,
    user_id: str | None = None,
) -> dict | None:
    """按 session_id 查询会话（含历史消息），可选 user_id 校验归属"""
    conversation = await get_conversation(db, session_id, user_id=user_id)
    if conversation is None:
        return None

    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation["session_id"])
        .order_by(Message.created_at.asc())
    )
    messages = [_message_to_dict(msg) for msg in messages_result.scalars().all()]

    return {
        "conversation": conversation,
        "messages": messages,
    }


async def save_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    extra_data: dict | None = None,
) -> dict:
    """保存一条消息到数据库，返回前端可直接消费的 dict"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        extra_data=extra_data or {},
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return _message_to_dict(message)


async def get_history_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 20,
) -> list[dict]:
    """获取某个会话的最新 N 条历史消息，按时间升序排列"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return [_message_to_dict(msg) for msg in result.scalars().all()]


async def delete_conversation(
    db: AsyncSession,
    session_id: str,
    user_id: str | None = None,
) -> bool:
    """按 session_id 删除会话及其所有消息，可选 user_id 校验归属"""
    where = [Conversation.session_id == session_id]
    if user_id is not None:
        where.append(Conversation.user_id == user_id)
    result = await db.execute(
        select(Conversation).where(*where)
    )
    conv = result.scalars().first()
    if conv is None:
        return False

    await db.delete(conv)
    await db.commit()
    return True


async def list_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """查询某个用户的所有会话，按更新时间倒序排列"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [_conversation_to_dict(conv) for conv in result.scalars().all()]


async def count_conversations(
    db: AsyncSession,
    user_id: str,
) -> int:
    """查询某个用户的会话总数"""
    result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )
    return result.scalar() or 0


async def update_conversation(
    db: AsyncSession,
    session_id: str,
    title: str | None = None,
    user_id: str | None = None,
) -> dict | None:
    """更新会话标题，可选 user_id 校验归属"""
    where = [Conversation.session_id == session_id]
    if user_id is not None:
        where.append(Conversation.user_id == user_id)
    result = await db.execute(
        select(Conversation).where(*where)
    )
    conv = result.scalars().first()
    if conv is None:
        return None

    if title is not None:
        conv.title = title

    await db.commit()
    await db.refresh(conv)
    return _conversation_to_dict(conv)
