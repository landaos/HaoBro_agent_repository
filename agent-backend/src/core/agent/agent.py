import asyncio
import json
import sys
import io
import threading
from asyncio import CancelledError
from collections.abc import AsyncGenerator

from langchain.agents import create_agent
# from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from langsmith import traceable
from requests import exceptions as requests_exceptions
from src.logger.logger import logger

from src.config import settings
from src.prompt.prompt_loader import load_prompt
from src.core.tools.app_launcher import launch_app
from src.core.tools.rag import rag_tool, current_user_id as _rag_user_id_ctx, current_kb_id as _rag_kb_id_ctx
from src.db.session import async_session_factory
from src.services.conversation import (
    get_conversation,
    get_conversation_with_messages,
    create_conversation,
    save_message,
)

# Windows 终端 GBK 编码兼容
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 历史消息 Token 预算 ──
MAX_HISTORY_TOKENS = 4000

def _count_tokens(text: str) -> int:
    """估算文本占用的 token 数（中文 1.5 字符/token）"""
    return int(len(text) / 1.5) + 4


def _truncate_history_by_tokens(
    messages: list[dict], max_tokens: int
) -> list[dict]:
    """从最新的消息开始往旧方向取，使总 token 不超过预算"""
    result: list[dict] = []
    total = 0
    for msg in reversed(messages):
        tokens = _count_tokens(msg["content"])
        if total + tokens > max_tokens:
            break
        result.insert(0, msg)
        total += tokens
    return result


# ── Agent 系统提示词 ──
SYSTEM_PROMPT = load_prompt('agent_prompt')

# ── 全局 Agent 实例（后台线程预热） ──
# 模块导入时立即启动后台初始化，不阻塞服务器启动
_agent_instance = None


def _init_agent_background():
    """后台线程：初始化模型（API 调用，毫秒级）。"""
    global _agent_instance
    logger.info("【agent】后台初始化模型中（API 模式，毫秒级）...")
    model = ChatTongyi(
            model_name=settings.chat_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            streaming=True,
            top_p=0.7,
        )
    # model = init_chat_model(
    #     "deepseek:deepseek-v4-flash", api_key=settings.deepseek_api_key
    # )
    _agent_instance = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[launch_app, rag_tool],
    )
    logger.info("【agent】Agent初始化完成")


threading.Thread(target=_init_agent_background, daemon=True).start()


# ── 后台保存助手消息（独立 task，不受请求 cancel scope 影响） ──
# 参考：ChatGPT / DeepSeek 等企业级方案将 DB 写入与请求生命周期解耦，
# 使用独立 asyncio task 确保用户断开后仍能完整保存消息。
async def _save_assistant_message(conv_id: str, content: str):
    """后台保存助手回复，完全脱离请求 cancel scope"""
    try:
        session = async_session_factory()
        try:
            async with session as db:
                await save_message(db, conv_id, "assistant", content)
                await db.commit()
        except Exception as e:
            logger.error(f"【agent】后台保存助手回复失败 | session={conv_id} | {e}")
    except Exception:
        pass  # 避免后台任务异常影响主流程


async def _prepare_conversation(
    session_id: str, user_id: str, query: str
) -> tuple[str, list]:
    """独立 task：查/建会话 + 保存用户消息 + 加载历史，返回 (conv_id, messages)"""
    async with async_session_factory() as db:
        logger.info(f"【agent】开始处理请求 | session={session_id} | query={query}")

        conversation = await get_conversation(db, session_id)
        if conversation is None:
            conversation = await create_conversation(db, session_id, user_id, query)
            logger.info(f"【agent】新建会话 | id={conversation['id']}")
        conv_id = conversation["session_id"]

        await save_message(db, conv_id, "user", query)

        full_data = await get_conversation_with_messages(db, session_id)
        history_msgs = full_data["messages"] if full_data else []

        if history_msgs and history_msgs[-1]["role"] == "user":
            history_msgs = history_msgs[:-1]

        history_msgs = _truncate_history_by_tokens(history_msgs, MAX_HISTORY_TOKENS)

        messages: list = []
        for msg in history_msgs:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=query))

        await db.commit()
        return conv_id, messages


@traceable
async def get_agent_stream_response(
    query: str,
    session_id: str,
    user_id: str,
    kb_id: int | None = None,
) -> AsyncGenerator[str, None]:
    """
    获取 Agent 流式响应（SSE 格式，前端可直接消费）

    流程：
      1. 查/建会话 → 2. 保存用户消息 → 3. 加载历史 → 提交并关闭 session
      → 4. Agent 流式执行 → 5. 用新 session 保存助手回复

    关键设计：流式输出前关闭 DB session，连接归还连接池。
    流式期间不持有任何 DB 连接，客户端断开不会污染连接池。
    参考：https://github.com/soliplex/soliplex/issues/670

    Yields:
      SSE 数据帧：type 为 start / response / done / error
    """
    # ── 阶段1：流式前的 DB 操作（独立 task，不受请求取消影响） ──
    # 使用 asyncio.create_task 确保即使极端情况下客户端在 Phase 1 期间断开，
    # 后台 task 仍能完整执行 commit + close，连接安全归还池子
    task = asyncio.create_task(
        _prepare_conversation(session_id, user_id, query)
    )
    try:
        conv_id, messages = await asyncio.shield(task)
    except CancelledError:
        # shield 保护了内部 task，task 继续运行，重新 await 取结果
        conv_id, messages = await task

    # ── 阶段2：流式输出（不持有任何 DB 连接，客户端断开不会污染连接池） ──
    full_response: list[str] = []
    was_cancelled = False  # 标记是否被用户中断
    try:
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        # 设置当前请求的 user_id，供 rag_tool 通过 contextvar 读取
        _rag_user_id_ctx.set(user_id)
        if kb_id is not None:
            _rag_kb_id_ctx.set(kb_id)

        # 等待后台模型预热完成，等待时发心跳保持连接
        while _agent_instance is None:
            await asyncio.sleep(1.0)
            yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"

        # create_agent 返回 CompiledStateGraph，使用 ainvoke 获取最终结果，
        # 然后手动逐字符流式输出。避免 stream_mode="messages" 把工具调用
        # 阶段的思考内容（如 HyDE 假设性文档）也泄露给前端
        # 带重试：DashScope 服务端偶尔会主动 RST 连接（ConnectionResetError），
        # ChatTongyi 内置 retry 仅匹配 HTTPError，不匹配 ConnectionError，需上层兜底
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES + 1):
            try:
                full_response = []
                result = await _agent_instance.ainvoke(
                    {"messages": messages},
                    config={"recursion_limit": 5},
                )
                # 取最后一条消息作为最终回答
                final_answer = result["messages"][-1].content
                full_response = [final_answer]
                for char in final_answer:
                    yield f"data: {json.dumps({'type': 'response', 'content': char}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.015)
                break  # 成功，跳出重试循环
            except (requests_exceptions.ConnectionError, ConnectionResetError) as e:
                if attempt >= MAX_RETRIES:
                    raise
                logger.warning(
                    f"【agent】连接断开，第{attempt+1}次重试 | session={session_id}"
                )
                # 通知前端丢弃之前收到的半截内容，准备接收新内容
                yield f"data: {json.dumps({'type': 'reset'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(2 ** (attempt + 1))

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        logger.info(f"【agent】请求处理完成 | session={session_id}")

    except CancelledError:
        # 客户端主动断开连接（如点击停止按钮），不视为错误
        was_cancelled = True
        logger.info(
            f"【agent】客户端断开连接，保存已生成内容 | session={session_id} "
            f"| 已生成 {len(''.join(full_response))} 字符"
        )
    except Exception as e:
        logger.error(f"【agent】用户请求处理异常 | session={session_id} | {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'session_id': session_id}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
    finally:
        # ── 阶段3：保存助手回复（独立后台任务，脱离请求 cancel scope） ──
        # 使用 asyncio.create_task() 创建完全独立的任务，不受 Starlette 取消影响
        if was_cancelled:
            partial = "".join(full_response)
            final_reply = f"{partial}\n\n> ⏸️ 回答已被中断" if partial else "⏸️ 回答已被中断"
        else:
            final_reply = "".join(full_response) or "抱歉，我暂时无法回答这个问题。"
        asyncio.create_task(_save_assistant_message(conv_id, final_reply))
