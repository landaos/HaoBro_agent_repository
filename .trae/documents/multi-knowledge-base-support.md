# 多知识库支持实施计划

## 背景

当前系统限制每个用户只能创建一个知识库（`knowledge_bases.py` 第 40-45 行硬编码校验）。前端已支持多知识库的 UI 和状态管理，ChatRequest 已包含 `kb_id` 字段，Agent 层也已接收 `kb_id` 参数。但 `kb_id` 在 Agent 层被丢弃，没有沿调用链传递到 RAG 检索层，导致向量检索只按 `user_id` 过滤，知识库之间数据无法隔离。

## 目标

- 移除"一个用户只能创建一个知识库"的限制
- 确保 RAG 检索同时按 `user_id` 和 `kb_id` 过滤，实现知识库级别数据隔离
- 不改动前端代码（前端已就绪）

## 数据流

```
前端 → POST /api/v1/chat { kb_id: 123 }
  → chat.py: ChatRequest.kb_id
  → agent.py: get_agent_stream_response(kb_id=123)
    → _rag_kb_id_ctx.set(123)          ← 新增
    → Agent 调用 rag_tool(query)
  → rag.py: rag_tool(query)
    → kid = current_kb_id.get()        ← 新增
    → rag_core(query, user_id, kb_id=123)
  → rag_core.py: retriever_documents(query, user_id, kb_id=123)
  → vector_store.py: get_retriever(query, user_id, kb_id=123)
    → filter = {'$and': [{'user_id': 'xxx'}, {'kb_id': 123}]}
```

## 修改清单（5 个文件，按依赖顺序）

### 步骤 1: `src/api/routers/knowledge_bases.py` — 移除单KB限制

删除第 40-45 行的限制检查：

```python
# 删除：
existing = await db.execute(
    select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
)
if existing.scalar_one_or_none():
    raise HTTPException(status_code=400, detail="每个用户只能创建一个知识库")
```

### 步骤 2: `src/core/rag/vector_store.py` — 底层加 kb_id 过滤

**A. `get_retriever()` 方法** — 签名增加 `kb_id`，使用 ChromaDB `$and` 组合过滤：

```python
async def get_retriever(self, query=None, user_id=None, kb_id=None):
    search_kwargs = {'k': chroma_config['k']}
    if user_id and kb_id:
        search_kwargs['filter'] = {'$and': [{'user_id': user_id}, {'kb_id': kb_id}]}
    elif user_id:
        search_kwargs['filter'] = {'user_id': user_id}
    elif kb_id:
        search_kwargs['filter'] = {'kb_id': kb_id}
    ...
    bm25_retriever = await self.get_bm25_retriever(user_id=user_id, kb_id=kb_id)
```

**B. `get_bm25_retriever()` 方法** — 签名增加 `kb_id`，加载文档时加 `kb_id` 过滤：

```python
async def get_bm25_retriever(self, user_id=None, kb_id=None):
    ...
    if user_id:
        where_filter = {'$and': [{'user_id': user_id}, {'kb_id': kb_id}]} if kb_id else {'user_id': user_id}
        raw_docs = await asyncio.to_thread(self.vectors_store.get, where=where_filter, ...)
```

### 步骤 3: `src/core/rag/rag_core.py` — 中间层传递 kb_id

**A. `retriever_documents()` 方法** — 签名增加 `kb_id`，传递给 `get_retriever()`：

```python
async def retriever_documents(self, query, user_id=None, kb_id=None):
    retriever = await self.vector_store.get_retriever(query, user_id, kb_id)
```

**B. `rag_core()` 方法** — 签名增加 `kb_id`，传递给 `retriever_documents()`：

```python
async def rag_core(self, query, user_id=None, kb_id=None):
    documents = await self.retriever_documents(query, user_id, kb_id)
```

### 步骤 4: `src/core/tools/rag.py` — Tool 层增加 contextvar

**A. 新增 contextvar：**

```python
current_kb_id: ContextVar[int | None] = ContextVar("current_kb_id", default=None)
```

**B. `rag_tool()` 读取并传递 kb_id：**

```python
async def rag_tool(query: str) -> str:
    uid = current_user_id.get()
    kid = current_kb_id.get()
    return await rag_service.rag_core(query, user_id=uid, kb_id=kid)
```

### 步骤 5: `src/core/agent/agent.py` — Agent 层设置 contextvar

**A. 导入新增：**

```python
from src.core.tools.rag import rag_tool, current_user_id as _rag_user_id_ctx, current_kb_id as _rag_kb_id_ctx
```

**B. 在 `get_agent_stream_response()` 中设置 kb_id：**

```python
_rag_user_id_ctx.set(user_id)
if kb_id is not None:
    _rag_kb_id_ctx.set(kb_id)
```

## 向后兼容

- 所有新增的 `kb_id` 参数都是 `Optional`（默认 `None`）
- 当 `kb_id` 为 `None` 时，行为与原来一致（仅按 `user_id` 过滤）
- 前端传 `kb_id` 时自动启用知识库隔离；不传时兼容旧逻辑

## 验证方式

1. 创建两个知识库（KB-A 和 KB-B），分别上传不同文档
2. 切换到 KB-A，提问：应只检索 KB-A 的文档
3. 切换到 KB-B，提问：应只检索 KB-B 的文档
4. 检查日志：`get_retriever` 的 filter 应包含 `{'$and': [{'user_id': '...'}, {'kb_id': N}]}`