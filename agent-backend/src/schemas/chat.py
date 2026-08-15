from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求（user_id 由后端从 JWT 提取，不再接受前端传参）"""
    session_id: str = Field(..., description="客户端生成的会话 ID，同一会话传相同值")
    message: str = Field(..., min_length=1, description="用户输入的消息")
    kb_id: int | None = Field(None, description="绑定的知识库 ID，不为空则只检索该知识库内容")


class SSEChunk(BaseModel):
    """SSE 流式数据块"""
    type: str = Field(..., description="数据块类型：start / response / done / error")
    content: str = Field("", description="响应内容")
    session_id: str = Field("", description="会话 ID")
