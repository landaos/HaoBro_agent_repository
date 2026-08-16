from langchain_core.tools import tool
from contextvars import ContextVar
from src.core.rag.rag_core import ragService

# 使用 contextvars 传递当前请求的 user_id 和 kb_id（线程安全）
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)
current_kb_id: ContextVar[int | None] = ContextVar("current_kb_id", default=None)

# 防止每次tool调用都重新建 Chroma、BM25、ChatModel、Chain，创建一个全局单例
_rag_service = None

def _get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = ragService()
    return _rag_service

@tool(description="当你认为需要检索内部知识库回答用户问题时使用该rag工具,输入问题,直接得到该问题结合经过rag检索和重排序的文档进行回答的结果,但是当输入问题在知识库内部检索到文档的相似度太低时rag检索失败,这时候请你直接回答用户问题并说明该问题在知识库中没有相似度达标的相关文档")
async def rag_tool(query: str) -> str:
    """使用rag工具回答用户问题"""
    rag_service = _get_rag_service()
    uid = current_user_id.get()
    kid = current_kb_id.get()
    return await rag_service.rag_core(query, user_id=uid, kb_id=kid)