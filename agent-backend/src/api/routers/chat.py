from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from src.logger.logger import logger

from src.core.agent.agent import get_agent_stream_response
from src.schemas.chat import ChatRequest
from src.auth.security import security, get_current_user_id

router = APIRouter()


@router.post("")
async def chat_stream(
    body: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    SSE 流式对话接口

    前端使用 fetch + ReadableStream 消费。
    user_id 从 JWT token 中提取，确保数据隔离安全。
    """
    user_id = await get_current_user_id(credentials)
    logger.info(f"【chat】收到对话请求 | session={body.session_id} user={user_id}")

    async def event_generator():
        async for sse_data in get_agent_stream_response(
            query=body.message,
            session_id=body.session_id,
            user_id=user_id,
            kb_id=body.kb_id,
        ):
            yield sse_data

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
