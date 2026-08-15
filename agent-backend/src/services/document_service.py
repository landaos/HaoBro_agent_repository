"""
document_service.py — 文档管理服务

负责：
  1. 文件上传、存储、持久化记录
  2. 触发文档处理流水线（加载 → 分块 → 向量化 → 入库）
  3. 文档列表、详情、删除（同步清理向量数据 + 本地文件）
"""
from __future__ import annotations

from pathlib import Path

from src.logger.logger import logger
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document
from src.schemas.document import DocumentResponse
from src.services.file_storage import FileStorageService, SUPPORTED_FILE_TYPES

from src.core.rag.document_processor import process_document
from src.core.rag.vector_store import VectorStoreService


class DocumentService:
    """文档管理服务"""

    def __init__(self):
        self.file_storage = FileStorageService()
        self.vector_store = VectorStoreService()

    # ------------------------------------------------------------
    # 上传文档（同步处理，保留兼容）
    # ------------------------------------------------------------

    async def upload(
        self,
        db: AsyncSession,
        user_id: int,
        kb_id: int,
        file_data: bytes,
        file_name: str,
        title: str | None = None,
    ) -> Document:
        """
        上传文档 → 校验 → 存储 → 创建记录 → 触发处理流水线。

        参数:
            db:        数据库会话
            user_id:   上传者用户 ID
            kb_id:     知识库 ID
            file_data: 文件二进制内容
            file_name: 原始文件名
            title:     文档标题（可选，不传则用文件名）

        返回:
            Document: 已创建的文档记录（status=pending）
        """
        # ── 1. 校验文件类型 ──
        file_type = self.file_storage.validate_file_type(file_name)
        if not file_type:
            raise ValueError(
                f"不支持的文件类型: {Path(file_name).suffix}。"
                f"仅支持: {', '.join(SUPPORTED_FILE_TYPES.keys())}"
            )

        # ── 2. 校验文件大小 ──
        is_valid, err_msg = self.file_storage.validate_file_size(len(file_data))
        if not is_valid:
            raise ValueError(err_msg)

        # ── 3. 存储文件 ──
        file_info = self.file_storage.save(file_data, file_name)

        # ── 4. 创建 Document 记录 ──
        doc = Document(
            kb_id=kb_id,
            title=title or Path(file_name).stem,
            file_name=file_name,
            file_path=file_info.file_path,
            file_size=file_info.file_size,
            file_type=file_type,
            status="pending",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info(f"文档记录已创建: id={doc.id}, file={file_name}")

        # ── 5. 触发处理流水线（同步，旧逻辑，保留兼容） ──
        try:
            absolute_path = self.file_storage.get_absolute_path(file_info.file_path)
            doc.status = "processing"
            await db.commit()

            result = await process_document(
                file_path=absolute_path,
                kb_id=kb_id,
                doc_id=doc.id,
                session=db,
                title=doc.title,
            )

            doc.status = "completed"
            doc.chunk_count = result.get("chunk_count", 0)
            await db.commit()
            logger.info(f"文档处理完成: doc_id={doc.id}, {result}")

        except Exception as e:
            # 先 rollback 清除事务失败状态，再更新 status
            await db.rollback()
            doc.status = "failed"
            await db.commit()
            logger.error(f"文档处理失败: doc_id={doc.id}, error={e}")
            # 不 re-raise，避免 get_db() 的 rollback 把 status='failed' 回滚掉
            # 前端会看到 failed 状态，用户可以手动点"重新处理"

        await db.refresh(doc)
        return doc

    # ------------------------------------------------------------
    # 创建记录（异步：仅保存文件+创建记录，不触发处理）
    # ------------------------------------------------------------

    async def create_record(
        self,
        db: AsyncSession,
        kb_id: int,
        file_data: bytes,
        file_name: str,
        title: str | None = None,
    ) -> Document:
        """仅保存文件并创建 Document 记录（status=pending），不触发处理流水线。"""
        file_type = self.file_storage.validate_file_type(file_name)
        if not file_type:
            raise ValueError(
                f"不支持的文件类型: {Path(file_name).suffix}。"
                f"仅支持: {', '.join(SUPPORTED_FILE_TYPES.keys())}"
            )

        is_valid, err_msg = self.file_storage.validate_file_size(len(file_data))
        if not is_valid:
            raise ValueError(err_msg)

        file_info = self.file_storage.save(file_data, file_name)

        doc = Document(
            kb_id=kb_id,
            title=title or Path(file_name).stem,
            file_name=file_name,
            file_path=file_info.file_path,
            file_size=file_info.file_size,
            file_type=file_type,
            status="pending",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info(f"文档记录已创建（异步）: id={doc.id}, file={file_name}")
        return doc

    # ------------------------------------------------------------
    # 查询文档
    # ------------------------------------------------------------

    async def get_by_id(self, db: AsyncSession, doc_id: int) -> Document | None:
        """按 ID 查询文档"""
        result = await db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        kb_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        file_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Document], int]:
        """
        分页查询文档列表。

        返回:
            (list[Document], total_count)
        """
        query = select(Document).where(Document.kb_id == kb_id)

        if status:
            query = query.where(Document.status == status)
        if file_type:
            query = query.where(Document.file_type == file_type)
        if search:
            query = query.where(Document.title.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = (
            query
            .order_by(desc(Document.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        docs = list(result.scalars().all())

        return docs, total

    # ------------------------------------------------------------
    # 删除文档
    # ------------------------------------------------------------

    async def delete(self, db: AsyncSession, doc_id: int) -> dict:
        """
        删除文档: 删向量 → 删本地文件 → 删记录。

        返回:
            {"status": "deleted", "deleted_vector_count": int}
        """
        doc = await self.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"文档不存在: id={doc_id}")

        # ── 1. 删除向量数据 ──
        deleted_vec_count = await self.vector_store.delete_by_doc_id(doc_id)

        # ── 2. 删除本地存储文件 ──
        if doc.file_path:
            try:
                self.file_storage.delete(doc.file_path)
            except Exception as e:
                logger.warning(f"删除本地文件失败: id={doc_id}, path={doc.file_path}, error={e}")

        # ── 3. 删除数据库记录 ──
        await db.delete(doc)
        await db.commit()

        logger.info(f"文档已删除: id={doc_id}, vectors={deleted_vec_count}")
        return {
            "status": "deleted",
            "deleted_vector_count": deleted_vec_count,
        }

    async def batch_delete(self, db: AsyncSession, doc_ids: list[int]) -> int:
        """批量删除文档，返回实际删除数量"""
        deleted = 0
        for doc_id in doc_ids:
            try:
                await self.delete(db, doc_id)
                deleted += 1
            except Exception as e:
                logger.warning(f"删除文档失败: id={doc_id}, error={e}")
        return deleted

    # ------------------------------------------------------------
    # 重新处理
    # ------------------------------------------------------------

    async def reprocess(self, db: AsyncSession, doc_id: int) -> Document:
        """重新处理文档（清空旧向量 → 重新加载/分块/向量化）"""
        doc = await self.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"文档不存在: id={doc_id}")

        await self.vector_store.delete_by_doc_id(doc_id)

        doc.status = "processing"
        doc.chunk_count = 0
        await db.commit()

        try:
            absolute_path = self.file_storage.get_absolute_path(doc.file_path) if doc.file_path else ""
            result = await process_document(
                file_path=absolute_path,
                kb_id=doc.kb_id,
                doc_id=doc.id,
                session=db,
                title=doc.title,
            )
            doc.status = "completed"
            doc.chunk_count = result.get("chunk_count", 0)
        except Exception as e:
            # 先 rollback 清除事务失败状态
            await db.rollback()
            doc.status = "failed"
            logger.error(f"重新处理失败: doc_id={doc_id}, error={e}")

        await db.commit()
        await db.refresh(doc)
        return doc


# ------------------------------------------------------------
# 后台异步处理函数（由 BackgroundTasks 调用）
# ------------------------------------------------------------

async def process_doc_in_background(
    file_path: str,
    kb_id: int,
    doc_id: int,
    user_id: str | None = None,
) -> None:
    """在后台执行文档处理流水线，自行管理 DB 会话。"""
    from src.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            if doc is None:
                logger.error(f"[后台] 文档不存在: id={doc_id}")
                return

            doc.status = "processing"
            await session.commit()

            pipeline_result = await process_document(
                file_path=file_path,
                kb_id=kb_id,
                doc_id=doc_id,
                session=session,
                user_id=user_id,
                title=doc.title,
            )

            doc.status = "completed"
            doc.chunk_count = pipeline_result.get("chunk_count", 0)
            await session.commit()
            logger.info(f"[后台] 文档处理完成: id={doc_id}, {pipeline_result}")

        except Exception as e:
            logger.error(f"[后台] 文档处理失败: id={doc_id}, error={e}")
            try:
                # 先 rollback 清除事务失败状态
                await session.rollback()
                result = await session.execute(
                    select(Document).where(Document.id == doc_id)
                )
                doc = result.scalar_one_or_none()
                if doc is not None:
                    doc.status = "failed"
                    await session.commit()
            except Exception as db_err:
                logger.error(f"[后台] 更新失败状态出错: {db_err}")
