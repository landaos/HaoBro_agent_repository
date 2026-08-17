import os, hashlib, aiofiles, asyncio, csv, io
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader, CSVLoader, UnstructuredExcelLoader

from src.logger.logger import logger


def get_project_root() -> str:
    """
    获取项目根目录
    :return: 项目根目录路径
    """
    # 从当前文件所在目录向上两级（app/utils -> app -> backend）
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(src_dir)
    return project_root

def get_abstract_path(relative_path: str) -> str:
    """
    根据传入的相对路径，获取项目根目录下 的绝对路径
    :param relative_path: 相对项目根目录的路径
    :return: 绝对路径
    """
    project_path = get_project_root()
    # 确保路径格式正确，处理不同操作系统的路径分隔符
    abstract_path = os.path.normpath(os.path.join(project_path, relative_path))
    return abstract_path

async def get_file_md5_hex(file_path: str) -> str:
    """获取文件的md5值"""
    # 处理路径，确保使用绝对路径
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    
    if not os.path.exists(abs_file_path):
        logger.error(f"【文档加载】路径不存在 | {abs_file_path}")
        return ""

    if not os.path.isfile(abs_file_path):
        logger.error(f"【文档加载】文件路径 {abs_file_path} 不是文件")
        return ""

    md5_object = hashlib.md5()
    chunk_size = 1024
    try:
        async with aiofiles.open(abs_file_path, "rb") as f:
            while chunk := await f.read(chunk_size):
                md5_object.update(chunk)
    except Exception as e:
        logger.error(f"【文档加载】读取文件 {abs_file_path} 时出错: {e}")
        return ""

    return md5_object.hexdigest()

async def listdir_allowed_type(path: str, allowed_types: tuple[str]) -> tuple:
    """
    获取指定目录下所有允许的文件类型
    :param path: 目录路径
    :param allowed_types: 允许的文件类型元组
    :return: 符合条件的文件路径列表
    """
    # 处理路径，确保使用绝对路径
    abs_path = get_abstract_path(path) if not os.path.isabs(path) else path
    
    if not os.path.exists(abs_path):
        logger.error(f"【文档加载】路劲不存在 | {abs_path}")
        return ()

    if not os.path.isdir(abs_path):
        logger.error(f"【文档加载】路径不是目录 | {abs_path}")
        return ()

    file_list = []
    for f in await asyncio.to_thread(os.listdir, abs_path):
        if f.endswith(allowed_types):
            file_path = os.path.join(abs_path, f)
            file_list.append(file_path)

    return tuple(file_list)



async def pdf_loader(file_path: str, password: str = None) -> list[Document]:
    """
    加载PDF文件内容
    :param file_path: PDF文件路径
    :param password: PDF密码（如果有）
    :return: PDF文件内容
    """
    # 处理路径，确保使用绝对路径
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    loader = PyPDFLoader(abs_file_path, password=password)
    return await asyncio.to_thread(loader.load)


async def txt_loader(file_path: str) -> list[Document]:
    """
    加载TXT文件内容
    :param file_path: TXT文件路径
    :return: TXT文件内容
    """
    # 处理路径，确保使用绝对路径
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    
    # 使用不同的编码加载文件
    encodings = ['utf-8', 'gbk']
    for encoding in encodings:
        try:
            loader = TextLoader(abs_file_path, encoding=encoding)
            return await asyncio.to_thread(loader.load)
        except Exception as e:
            logger.error(f"【文档加载】TXT编码失败 | {encoding} | {abs_file_path} | {e}")
            continue
    # 所有编码都失败，返回空列表
    return []

async def word_loader(file_path: str) -> list[Document]:
    """
    加载WORD文件内容
    :param file_path: WORD文件路径
    :return: WORD文件内容
    """
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    try:
        loader = UnstructuredWordDocumentLoader(abs_file_path, mode="single")
        return await asyncio.to_thread(loader.load)
    except Exception as e:
        logger.error(f"【文档加载】加载文件 {abs_file_path} 时出错: {e}")
        return []

async def markdown_loader(file_path: str) -> list[Document]:
    """
    加载Markdown文件内容
    :param file_path: Markdown文件路径
    :return: Markdown文件内容
    """
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    try:
        loader = UnstructuredMarkdownLoader(abs_file_path, mode="single")
        return await asyncio.to_thread(loader.load)
    except Exception as e:
        logger.error(f"【文档加载】Markdown加载失败 | {abs_file_path} | {e}")
        return []


async def ppt_loader(file_path: str) -> list[Document]:
    """
    加载PPT/PPTX文件内容
    :param file_path: PPT文件路径
    :return: PPT文件内容
    """
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    try:
        loader = UnstructuredPowerPointLoader(abs_file_path, mode="single")
        return await asyncio.to_thread(loader.load)
    except Exception as e:
        logger.error(f"【文档加载】PPT加载失败 | {abs_file_path} | {e}")
        return []


async def csv_loader(file_path: str) -> list[Document]:
    """
    加载 CSV 文件，每行作为一个 Document（避免默认 CSVLoader 一行一个 Document 导致 1000+ 行时性能极差）。
    按 100 行一批合并为一个 Document，减少分块和 embedding 开销。
    """
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    try:
        # 尝试多种编码读取
        content = None
        for encoding in ['utf-8', 'gbk', 'utf-8-sig']:
            try:
                async with aiofiles.open(abs_file_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue
        if content is None:
            logger.error(f"【文档加载】CSV编码失败 | {abs_file_path}")
            return []

        reader = csv.reader(io.StringIO(content))
        header = next(reader, None)
        if header is None:
            return []

        rows = list(reader)
        batch_size = 100
        documents = []
        source_name = os.path.basename(abs_file_path)

        for batch_start in range(0, len(rows), batch_size):
            batch_rows = rows[batch_start : batch_start + batch_size]
            lines = [",".join(header)]
            lines.extend(",".join(row) for row in batch_rows)
            batch_text = "\n".join(lines)
            doc = Document(
                page_content=batch_text,
                metadata={"source": abs_file_path, "source_file": source_name, "row_range": f"{batch_start + 1}-{batch_start + len(batch_rows)}"},
            )
            documents.append(doc)

        logger.info(f"【文档加载】CSV加载完成 | {abs_file_path} | {len(rows)}行 → {len(documents)}个Document")
        return documents
    except Exception as e:
        logger.error(f"【文档加载】CSV加载失败 | {abs_file_path} | {e}")
        return []


async def excel_loader(file_path: str) -> list[Document]:
    """加载 Excel 文件（.xlsx/.xls），使用 UnstructuredExcelLoader"""
    abs_file_path = get_abstract_path(file_path) if not os.path.isabs(file_path) else file_path
    try:
        loader = UnstructuredExcelLoader(abs_file_path, mode="elements")
        return await asyncio.to_thread(loader.load)
    except Exception as e:
        logger.error(f"【文档加载】Excel加载失败 | {abs_file_path} | {e}")
        return []


async def generate_table_summary(file_path: str) -> str | None:
    """用 AI 生成表格文件的内容摘要，用于文档级召回的标题匹配"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ('.csv', '.xlsx', '.xls'):
        return None

    try:
        if ext == '.csv':
            docs = await csv_loader(file_path)
        else:
            docs = await excel_loader(file_path)
        if not docs:
            return None

        # 取前 3000 字符作为摘要生成的输入
        sample_text = "\n".join(doc.page_content[:500] for doc in docs[:6])[:3000]
        if not sample_text.strip():
            return None

        from src.config import settings
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        summary_model = ChatTongyi(
            model_name=settings.chat_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            streaming=False,
            top_p=0.7,
        )
        summary_prompt = PromptTemplate.from_template(
            "请根据以下表格数据的前几行，用一句话（不超过30字）概括这个表格的内容主题和主要数据范围，"
            "用于作为文档标题帮助检索：\n\n{table_sample}\n\n一句话概括："
        )
        chain = summary_prompt | summary_model | StrOutputParser()
        summary = await chain.ainvoke({"table_sample": sample_text})
        logger.info(f"【表格摘要】生成成功 | {file_path} | {summary}")
        return summary.strip()
    except Exception as e:
        logger.warning(f"【表格摘要】生成失败 | {file_path} | {e}")
        return None


async def load_document(file_path: str) -> list[Document]:
    """根据文件扩展名分发到对应的加载器（统一入口）"""
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
    elif file_path.endswith(".csv"):
        return await csv_loader(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return await excel_loader(file_path)
    return []