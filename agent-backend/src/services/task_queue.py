# ============================================
# task_queue.py - 异步任务队列
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 背景：RAG 文档入库（PDF 解析 → 分块 → Embedding → 写入 PGVector）
# 是耗时操作（一份 100 页 PDF 可能需要 10-30 秒），不能阻塞 API。
# 需要异步任务队列在后台处理。
#
# 一、选型建议：
#    - arq（推荐）：轻量级，基于 Redis，比 Celery 简单 10 倍
#    - celery：功能全面但重，中小企业杀鸡用牛刀
#    - 简单方案：asyncio.create_task + 状态标记（不做队列，简单场景用）
#
# 二、arq 实现要点：
#
#    from arq import create_pool
#    from arq.connections import RedisSettings
#
#    class TaskQueue:
#        def __init__(self, redis_pool: arq.ArqRedis):
#            self.pool = redis_pool
#
#        async def enqueue_ingest_document(self, file_path: str, collection: str) -> str:
#            """将文档入库任务加入队列，返回任务 ID"""
#            job = await self.pool.enqueue_job(
#                "ingest_document",        # 对应 worker 中的函数名
#                file_path=file_path,
#                collection=collection,
#            )
#            return job.job_id
#
#        async def get_task_status(self, job_id: str) -> dict:
#            """查询任务状态"""
#            job = await self.pool.get_job(job_id)
#            return {"status": job.status, "result": job.result, "error": job.error}
#
#    # Worker 函数（在独立的 worker 进程中运行）
#    async def ingest_document(ctx, file_path: str, collection: str):
#        # 1. 解析文档
#        # 2. 分块
#        # 3. Embedding
#        # 4. 写入 PGVector
#        pass  # 实际逻辑在 core/rag/document_loader.py 中
#
# 三、API 接口（在 api/routers 中）：
#    POST /documents/upload
#      → 接收文件 → 保存到临时目录 → 入队 → 返回 task_id
#    GET /documents/tasks/{task_id}
#      → 查询处理状态（pending/processing/done/error）
#
# ═══════════════════════════════════════════
# 启动 worker：
#   arq src.worker.WorkerSettings
# 或
#   python -m src.worker
#
# 依赖（在 pyproject.toml 中加）：
#   "arq>=0.26"
# ═══════════════════════════════════════════
