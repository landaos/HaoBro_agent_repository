"""
document_processor.py — 文档处理流水线

负责：加载文档 → 分块 → 向量化 → 存入 Chroma
"""
import os

from src.logger.logger import logger
from src.core.rag.vector_store import VectorStoreService
from src.core.rag.document_loader import pdf_loader, txt_loader, markdown_loader, ppt_loader, word_loader


async def _load_document(file_path: str):
    """根据文件扩展名加载文档"""
    if file_path.endswith(".txt"):
        return await txt_loader(file_path)
    elif file_path.endswith(".pdf"):
        return await pdf_loader(file_path)
    elif file_path.endswith(".md"):
        return await markdown_loader(file_path)
    elif file_path.endswith(".pptx"):
        return await ppt_loader(file_path)
    elif file_path.endswith(".docx"):
        return await word_loader(file_path)
    return []


async def process_document(
    file_path: str,
    kb_id: int,
    doc_id: int,
    session,
    user_id: str | None = None,
    title: str | None = None,
) -> dict:
    """
    处理文档完整流水线：加载 → 分块 → 打元数据 → 入库

    参数:
        file_path: 文件绝对路径
        kb_id:     知识库 ID
        doc_id:    文档 ID
        session:   数据库会话
        user_id:   用户 ID（用于隔离）
        title:     文档标题（拼入分块正文，使标题词可被检索）

    返回:
        {"chunk_count": int}
    """
    vector_store = VectorStoreService()

    # 1. 加载文档
    documents = await _load_document(file_path)
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

    # 4. 入库
    import asyncio
    await asyncio.to_thread(vector_store.vectors_store.add_documents, split_docs)
    logger.info(f"【文档处理】成功 | doc_id={doc_id}, kb_id={kb_id}, chunks={len(split_docs)}")
    return {"chunk_count": len(split_docs)}