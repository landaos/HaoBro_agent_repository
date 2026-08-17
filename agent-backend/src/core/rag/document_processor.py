"""
document_processor.py — 文档处理流水线

负责：MD5去重 → 加载文档 → 分块 → 打元数据 → 向量化入库
"""
import os

from src.logger.logger import logger
from src.core.rag.vector_store import VectorStoreService
from src.core.rag.document_loader import load_document, get_file_md5_hex


async def process_document(
    file_path: str,
    kb_id: int,
    doc_id: int,
    session,
    user_id: str | None = None,
    title: str | None = None,
) -> dict:
    """
    处理文档完整流水线：MD5去重 → 加载 → 分块 → 打元数据 → 入库

    参数:
        file_path: 文件绝对路径
        kb_id:     知识库 ID
        doc_id:    文档 ID
        session:   数据库会话
        user_id:   用户 ID（用于隔离）
        title:     文档标题（拼入分块正文，使标题词可被检索）

    返回:
        {"chunk_count": int, "skipped": bool}
    """
    vector_store = VectorStoreService()

    # 0. MD5 去重
    md5_hex = await get_file_md5_hex(file_path)
    if md5_hex and await vector_store.check_md5_hex(md5_hex):
        logger.info(f"【文档处理】MD5重复，跳过入库 | doc_id={doc_id}, file={os.path.basename(file_path)}")
        return {"chunk_count": 0, "skipped": True}

    # 1. 加载文档
    documents = await load_document(file_path)
    if not documents:
        logger.warning(f"【文档处理】文件加载为空 | {file_path}")
        return {"chunk_count": 0}

    # 2. 分块
    split_docs = await vector_store.spliter.split_documents(documents)

    # 3. 打元数据
    source_name = os.path.basename(file_path)
    # 标题作为前缀拼入正文，确保按标题提问也能检索到
    title_prefix = title or os.path.splitext(source_name)[0]
    for i, doc in enumerate(split_docs, 1):
        doc.metadata["chunk_index"] = i
        doc.metadata["source_file"] = source_name
        doc.metadata["doc_id"] = doc_id
        doc.metadata["kb_id"] = kb_id
        if user_id:
            doc.metadata["user_id"] = user_id
        if title_prefix:
            doc.page_content = f"【文档标题】{title_prefix}\n{doc.page_content}"

    if not split_docs:
        logger.warning(f"【文档处理】分块为空 | {file_path}")
        return {"chunk_count": 0}

    # 4. 入库（embedding 调用阿里云接口偶发网络抖动，失败自动重试）
    import asyncio
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            await asyncio.to_thread(vector_store.vector_store.add_documents, split_docs)
            break
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"【文档处理】入库失败（已重试 {max_retries} 次） | doc_id={doc_id}, error={e}")
                raise
            logger.warning(f"【文档处理】入库失败，第 {attempt} 次重试 | doc_id={doc_id}, error={e}")
            await asyncio.sleep(2 * attempt)

    # 5. 保存 MD5 防止重复入库
    if md5_hex:
        await vector_store.save_md5_hex(md5_hex)

    logger.info(f"【文档处理】成功 | doc_id={doc_id}, kb_id={kb_id}, chunks={len(split_docs)}")
    return {"chunk_count": len(split_docs)}