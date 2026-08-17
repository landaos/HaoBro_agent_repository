import asyncio
import sys
import os
import tempfile

from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import aiofiles
from aiofiles import os as aio_os

from langchain_core.documents import Document
from src.core.rag.text_spliter import AsyncTextSplitter
from src.configs.config_loader import vector_store_config
from src.core.agent.factory import embed_model
from src.core.rag.document_loader import (
    listdir_allowed_type, get_file_md5_hex,
    get_project_root, load_document,
)
from src.logger.logger import logger

# ============================================================
# PGVector 导入
# ============================================================
from langchain_postgres import PGVector
from src.config import settings
from sqlalchemy import select, func, delete as sa_delete


def get_abstract_path(relative_path: str) -> str:
    """
    根据传入的相对路径，获取项目根目录下的绝对路径
    :param relative_path: 相对项目根目录的路径
    :return: 绝对路径
    """
    project_path = get_project_root()
    abstract_path = os.path.normpath(os.path.join(project_path, relative_path))
    return abstract_path


class VectorStoreService:
    def __init__(self):
        # ============================================================
        # PGVector 初始化（替代 Chroma）
        # ============================================================
        self.config = vector_store_config
        self.vector_store = PGVector(
            embeddings=embed_model,
            collection_name=self.config['collection_name'],
            connection=settings.pgvector_url,
            use_jsonb=True,
        )
        self.spliter = AsyncTextSplitter(
            chunk_size=self.config['chunk_size'],
            chunk_overlap=self.config['chunk_overlap'],
            separators=self.config['separators'],
            embedding_model=embed_model
        )

    # ── 原 Chroma 初始化代码（已注释） ──────────────────────────
    # def __init__(self):
    #     persist_dir = get_abstract_path(chroma_config['persist_directory'])
    #     self.vectors_store = Chroma(
    #         collection_name=chroma_config['collection_name'],
    #         embedding_function=embed_model,
    #         persist_directory=persist_dir,
    #     )
    #     self.spliter = AsyncTextSplitter(...)

    # ============================================================
    # 过滤条件构建器
    # ============================================================
    def _build_filter(self, user_id=None, kb_id=None, doc_id=None):
        """构建 PGVector dict 过滤条件（用于 as_retriever 的 search_kwargs）

        PGVector 的 _handle_field_filter 使用 jsonb_path_match 做 JSONB 比较，
        能正确处理整数/字符串类型匹配。

        注意：返回 dict 而非 SQLAlchemy 表达式，因为 PGVector 内部会对
        SQLAlchemy 表达式做 boolean 判断（if filter:），触发 SQLAlchemy 2.0
        的 "Boolean value of this clause is not defined" 错误。
        """
        filter_dict = {}
        if user_id:
            filter_dict['user_id'] = user_id
        if kb_id is not None:
            filter_dict['kb_id'] = kb_id
        if doc_id is not None:
            filter_dict['doc_id'] = doc_id
        return filter_dict if filter_dict else None

    def _dict_to_sql_filter(self, filter_dict):
        """将 dict filter 转换为 SQLAlchemy 表达式（用于原始 SQL 查询）"""
        if filter_dict is None:
            return None
        return self.vector_store._create_filter_clause(filter_dict)

    # ============================================================
    # BM25 关键词检索器
    # ============================================================
    async def get_bm25_retriever(self, user_id: str | None = None, kb_id: int | None = None):
        """构建 BM25 关键词检索器，支持按 user_id 和 kb_id 过滤"""
        all_docs = []

        if user_id:
            # 多用户模式：从 PGVector 按 user_id 和 kb_id 过滤加载文档
            filter_dict = self._build_filter(user_id=user_id, kb_id=kb_id)
            filter_clause = self._dict_to_sql_filter(filter_dict)
            collection = self.vector_store.EmbeddingStore

            def _fetch():
                stmt = select(collection.document, collection.cmetadata)
                if filter_clause is not None:
                    stmt = stmt.where(filter_clause)
                with self.vector_store._engine.connect() as conn:
                    rows = conn.execute(stmt).fetchall()
                return rows

            rows = await asyncio.to_thread(_fetch)
            for row in rows:
                all_docs.append(Document(
                    page_content=row.document,
                    metadata=row.cmetadata or {},
                ))

            # ── 原 Chroma 代码 ──
            # where_filter: dict = {"user_id": user_id}
            # if kb_id is not None:
            #     where_filter = {"$and": [{"user_id": user_id}, {"kb_id": kb_id}]}
            # raw_docs = await asyncio.to_thread(
            #     self.vectors_store.get,
            #     where=where_filter,
            #     include=["documents", "metadatas"],
            # )
            # if raw_docs and raw_docs.get("ids"):
            #     for i in range(len(raw_docs["ids"])):
            #         all_docs.append(Document(
            #             page_content=raw_docs["documents"][i],
            #             metadata=raw_docs["metadatas"][i] if raw_docs["metadatas"] else {},
            #         ))
        else:
            # 无用户隔离模式：从磁盘加载所有文件（兼容旧逻辑）
            allowed_file_path: tuple[str] = await listdir_allowed_type(
                self.config['data_path'],
                tuple(self.config['allow_knowledge_file_types'])
            )
            file_paths = list(allowed_file_path)

            for file_path in file_paths:
                documents = await self.get_file_document(file_path)
                if documents:
                    split_docs = await self.spliter.split_documents(documents)
                    for i, doc in enumerate(split_docs, 1):
                        doc.metadata["source_file"] = os.path.basename(doc.metadata.get("source", file_path))
                        doc.metadata["chunk_index"] = i
                    all_docs.extend(split_docs)

        if all_docs:
            bm25_retriever = BM25Retriever.from_documents(
                documents=all_docs,
                k=self.config['k']
            )
            return bm25_retriever
        else:
            return None

    # ============================================================
    # 混合检索器（向量 + BM25）
    # ============================================================
    async def get_retriever(self, query: str = None, user_id: str | None = None, kb_id: int | None = None):
        # 构建 PGVector dict 过滤条件（避免 SQLAlchemy boolean 判断错误）
        filter_dict = self._build_filter(user_id=user_id, kb_id=kb_id)

        search_kwargs = {'k': self.config['k']}
        if filter_dict is not None:
            search_kwargs['filter'] = filter_dict

        vector_retriever = self.vector_store.as_retriever(
            search_type='similarity',
            search_kwargs=search_kwargs
        )

        bm25_retriever = await self.get_bm25_retriever(user_id=user_id, kb_id=kb_id)

        if bm25_retriever:
            weights = await self.get_dynamic_weights(query)
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=weights
            )
            return ensemble_retriever
        else:
            return vector_retriever

    # ============================================================
    # 动态权重（根据查询长度调整向量/BM25 权重）
    # ============================================================
    @staticmethod
    async def get_dynamic_weights(query: str = None):
        default_vector_weights = 0.5
        default_bm25_weights = 0.5

        if not query:
            return [default_vector_weights, default_bm25_weights]

        query_length = len(query)
        query_words = len(query.split())

        if query_length > 50:
            vector_weights = 0.7
            bm25_weights = 0.3
        elif query_length < 20:
            vector_weights = 0.3
            bm25_weights = 0.7
        else:
            vector_weights = 0.5
            bm25_weights = 0.5

        if query_words > 0:
            bili = query_words / query_length
            if bili > 0.1:
                bm25_weights = min(bm25_weights + 0.1, 0.7)
                vector_weights = max(bm25_weights - 0.1, 0.3)
        return [vector_weights, bm25_weights]

    # ============================================================
    # MD5 去重
    # ============================================================
    async def check_md5_hex(self, check_md5_for: str) -> bool:
        md5_path = get_abstract_path(self.config['md5_hex_store'])
        md5_dir = os.path.dirname(md5_path)
        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir, exist_ok=True)
        if not await aio_os.path.exists(md5_path):
            async with aiofiles.open(md5_path, 'w', encoding="utf-8") as f:
                pass
            return False

        async with aiofiles.open(md5_path, 'r', encoding='utf-8') as f:
            async for line in f:
                if line.strip() == check_md5_for:
                    return True
            return False

    async def save_md5_hex(self, md5_hex: str):
        async with aiofiles.open(get_abstract_path(self.config['md5_hex_store']), 'a', encoding="utf-8") as f:
            await f.write(md5_hex + '\n')

    # ============================================================
    # 文件加载（统一入口，委托给 document_loader.load_document）
    # ============================================================
    async def get_file_document(self, read_path: str) -> list[Document]:
        return await load_document(read_path)

    # ============================================================
    # 文档入库（保持了完整的分块元数据：source_file/chunk_index/user_id/kb_id/doc_id）
    # ============================================================
    async def store_document(self, files: list = None, user_id: str = None):
        files_path = []
        if files:
            for file in files:
                tempfile_path = await asyncio.to_thread(
                    tempfile.NamedTemporaryFile,
                    suffix=file.split('.')[-1],
                    delete=False
                )
                content = await file.read()
                await asyncio.to_thread(tempfile_path.write, content)
                files_path.append(tempfile_path.name)
        else:
            allowed_file_path: tuple[str] = await listdir_allowed_type(
                self.config['data_path'],
                tuple(self.config['allow_knowledge_file_types'])
            )
            files_path = list(allowed_file_path)

        for file_path in files_path:
            md5_hex = await get_file_md5_hex(file_path)
            if await self.check_md5_hex(md5_hex):
                logger.info(f"【向量库】文件已存在，跳过入库 | {file_path}")
                if files:
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                continue

            try:
                documents: list[Document] = await self.get_file_document(file_path)
                if not documents:
                    logger.error(f"向量数据库加载文档{file_path}为空，跳过入库")
                    if files:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                    continue

                # 切分文档
                documents: list[Document] = await self.spliter.split_documents(documents)

                # 给分块文档加上分块索引和源头文件名
                for i, doc in enumerate(documents, 1):
                    doc.metadata["chunk_index"] = i
                    doc.metadata["source_file"] = os.path.basename(doc.metadata["source"])

                if not documents:
                    logger.error(f"【向量库】文档切分为空，跳过入库 | {file_path}")
                    if files:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                    continue

                # 注入 user_id 作为元数据
                if user_id:
                    for doc in documents:
                        doc.metadata['user_id'] = user_id

                # PGVector 入库（同步方法，用 asyncio.to_thread 包装）
                await asyncio.to_thread(
                    self.vector_store.add_documents,
                    documents
                )

                # 保存 md5_hex
                await self.save_md5_hex(md5_hex)
                logger.info(f"向量数据库文件{file_path}入库成功.md5值{md5_hex}已经成功保存")

                if files:
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")

            except Exception as e:
                logger.error(f"【向量库】文档入库异常 | {file_path} | {e}")
                if files:
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                continue

    # ============================================================
    # 删除操作
    # ============================================================
    async def delete_user_documents(self, user_id: str):
        """删除指定用户的所有向量"""
        try:
            filter_dict = self._build_filter(user_id=user_id)
            filter_clause = self._dict_to_sql_filter(filter_dict)
            def _delete():
                with self.vector_store._engine.connect() as conn:
                    with conn.begin():
                        conn.execute(sa_delete(self.vector_store.EmbeddingStore).where(filter_clause))
            await asyncio.to_thread(_delete)
            logger.info(f"【向量库】用户文档已删除 | user={user_id}")
        except Exception as e:
            logger.error(f"【向量库】用户{user_id}的文档删除出现异常{e}")
            raise

    async def delete_all_documents(self):
        """删除向量数据库中所有文档，并清空 MD5 记录"""
        try:
            # 使用 SQLAlchemy 直接删除所有行
            def _delete_all():
                with self.vector_store._engine.connect() as conn:
                    with conn.begin():
                        conn.execute(sa_delete(self.vector_store.EmbeddingStore))

            await asyncio.to_thread(_delete_all)
            logger.info("【向量库】所有文档已清空")
        except Exception as e:
            logger.error(f"【向量库】清空所有文档异常 | {e}")
            raise
        try:
            # 清空 MD5 记录文件
            md5_path = get_abstract_path(self.config['md5_hex_store'])
            async with aiofiles.open(md5_path, 'w', encoding='utf-8') as f:
                await f.truncate(0)
            logger.info("【向量库】MD5记录已清空")
        except Exception as e:
            logger.error(f"【向量库】清空MD5记录异常 | {e}")

    async def delete_by_doc_id(self, doc_id: int) -> int:
        """删除指定 doc_id 的所有向量，返回删除数量"""
        try:
            filter_dict = self._build_filter(doc_id=doc_id)
            filter_clause = self._dict_to_sql_filter(filter_dict)

            # 先计数
            def _count():
                collection = self.vector_store.EmbeddingStore
                stmt = select(func.count()).select_from(collection).where(filter_clause)
                with self.vector_store._engine.connect() as conn:
                    return conn.execute(stmt).scalar()
            count = await asyncio.to_thread(_count)

            # 再删除
            def _delete():
                with self.vector_store._engine.connect() as conn:
                    with conn.begin():
                        conn.execute(sa_delete(self.vector_store.EmbeddingStore).where(filter_clause))
            await asyncio.to_thread(_delete)
            logger.info(f"【向量库】已删除 doc_id={doc_id} 的 {count} 条向量")
            return count

            # ── 原 Chroma 代码 ──
            # all_data = await asyncio.to_thread(self.vectors_store.get, include=["metadatas"])
            # ids_to_delete = []
            # for i, meta in enumerate(all_data.get("metadatas", []) if all_data else []):
            #     if meta and meta.get("doc_id") == doc_id:
            #         ids_to_delete.append(all_data["ids"][i])
            # if ids_to_delete:
            #     await asyncio.to_thread(self.vectors_store.delete, ids=ids_to_delete)
            # return len(ids_to_delete)
        except Exception as e:
            logger.error(f"【向量库】删除 doc_id={doc_id} 的向量异常: {e}")
            return 0

    async def delete_by_kb_id(self, kb_id: int) -> int:
        """删除指定 kb_id 的所有向量，返回删除数量"""
        try:
            filter_dict = self._build_filter(kb_id=kb_id)
            filter_clause = self._dict_to_sql_filter(filter_dict)

            def _count():
                collection = self.vector_store.EmbeddingStore
                stmt = select(func.count()).select_from(collection).where(filter_clause)
                with self.vector_store._engine.connect() as conn:
                    return conn.execute(stmt).scalar()
            count = await asyncio.to_thread(_count)

            def _delete():
                with self.vector_store._engine.connect() as conn:
                    with conn.begin():
                        conn.execute(sa_delete(self.vector_store.EmbeddingStore).where(filter_clause))
            await asyncio.to_thread(_delete)
            logger.info(f"【向量库】已删除 kb_id={kb_id} 的 {count} 条向量")
            return count

            # ── 原 Chroma 代码 ──
            # all_data = await asyncio.to_thread(self.vectors_store.get, include=["metadatas"])
            # ids_to_delete = []
            # for i, meta in enumerate(all_data.get("metadatas", []) if all_data else []):
            #     if meta and meta.get("kb_id") == kb_id:
            #         ids_to_delete.append(all_data["ids"][i])
            # if ids_to_delete:
            #     await asyncio.to_thread(self.vectors_store.delete, ids=ids_to_delete)
            # return len(ids_to_delete)
        except Exception as e:
            logger.error(f"【向量库】删除 kb_id={kb_id} 的向量异常: {e}")
            return 0

    # ============================================================
    # 文档级召回（按 chunk_index 排序返回全部分块）
    # ============================================================
    async def get_documents_by_doc_id(self, doc_id: int, user_id: str | None = None) -> list[Document]:
        """按 doc_id 获取该文档的全部分块（用于文档级召回）

        按 chunk_index 升序返回，保证文档原始顺序。
        """
        try:
            filter_dict = self._build_filter(doc_id=doc_id, user_id=user_id)
            filter_clause = self._dict_to_sql_filter(filter_dict)
            collection = self.vector_store.EmbeddingStore

            def _fetch():
                stmt = select(collection.document, collection.cmetadata).where(filter_clause)
                with self.vector_store._engine.connect() as conn:
                    rows = conn.execute(stmt).fetchall()
                return rows

            rows = await asyncio.to_thread(_fetch)
            docs = []
            for row in rows:
                docs.append(Document(
                    page_content=row.document,
                    metadata=row.cmetadata or {},
                ))
            docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))
            return docs

            # ── 原 Chroma 代码 ──
            # all_data = await asyncio.to_thread(
            #     self.vectors_store.get,
            #     include=["documents", "metadatas"],
            # )
            # docs = []
            # if not all_data or not all_data.get("ids"):
            #     return docs
            # for i in range(len(all_data["ids"])):
            #     meta = all_data["metadatas"][i] if all_data["metadatas"] else {}
            #     if not meta or meta.get("doc_id") != doc_id:
            #         continue
            #     if user_id and meta.get("user_id") != user_id:
            #         continue
            #     docs.append(Document(
            #         page_content=all_data["documents"][i],
            #         metadata=meta,
            #     ))
            # docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))
            # return docs
        except Exception as e:
            logger.error(f"【向量库】获取 doc_id={doc_id} 的文档分块异常: {e}")
            return []


# 兼容旧代码的别名
VectorStore = VectorStoreService