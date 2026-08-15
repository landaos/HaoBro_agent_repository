import asyncio
import sys
import os
import tempfile

from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


import aiofiles
from aiofiles import os as aio_os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.core.rag.text_spliter import  AsyncTextSplitter
from src.configs.config_loader import chroma_config
from src.core.agent.factory import embed_model
from src.core.rag.document_loader import  pdf_loader, txt_loader, listdir_allowed_type, get_file_md5_hex, markdown_loader, \
    ppt_loader, word_loader, get_project_root
from src.logger.logger import logger

def get_abstract_path(relative_path: str) -> str:
    """
    根据传入的相对路径，获取项目根目录下的绝对路径
    :param relative_path: 相对项目根目录的路径
    :return: 绝对路径
    """
    project_path = get_project_root()
    # 确保路径格式正确，处理不同操作系统的路径分隔符
    abstract_path = os.path.normpath(os.path.join(project_path, relative_path))
    return abstract_path

class VectorStoreService:
    def __init__(self):
        persist_dir=get_abstract_path(chroma_config['persist_directory'])
        self.vectors_store = Chroma(
            collection_name=chroma_config['collection_name'],
            embedding_function=embed_model,
            persist_directory=persist_dir,
        )     
        self.spliter=AsyncTextSplitter(
            chunk_size=chroma_config['chunk_size'],
            chunk_overlap=chroma_config['chunk_overlap'],
            separators=chroma_config['separators'],
            embedding_model=embed_model
        )

    async def get_bm25_retriever(self, user_id: str | None = None):
        """构建 BM25 关键词检索器，支持按 user_id 过滤"""
        all_docs = []

        if user_id:
            # 多用户模式：从向量库按 user_id 过滤加载文档
            raw_docs = await asyncio.to_thread(
                self.vectors_store.get,
                where={"user_id": user_id},
                include=["documents", "metadatas"],
            )
            if raw_docs and raw_docs.get("ids"):
                for i in range(len(raw_docs["ids"])):
                    all_docs.append(Document(
                        page_content=raw_docs["documents"][i],
                        metadata=raw_docs["metadatas"][i] if raw_docs["metadatas"] else {},
                    ))
        else:
            # 无用户隔离模式：从磁盘加载所有文件（兼容旧逻辑）
            allowed_file_path: tuple[str] = await listdir_allowed_type(
                chroma_config['data_path'],
                tuple(chroma_config['allow_knowledge_file_types'])
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
                k=chroma_config['k']
            )
            return bm25_retriever
        else:
            return None

    async def _get_all_documents(self) -> list[Document]:

        all_docs =await asyncio.to_thread( 
            self.vectors_store.get,
            include=['documemnts','metadatas'] 
        )
        documents=[]
        for i,doc in enumerate(all_docs['documents']):
            metadata=all_docs['metadatas'][i] if i <len(all_docs['metadatas']) else {}
            documents.append(Document(page_content=doc,metadata=metadata))
        return documents

    async def  get_retriever(self,query:str=None,user_id:str|None=None):
        search_kwargs = {'k': chroma_config['k']}
        if user_id:
            search_kwargs['filter'] = {'user_id': user_id}
        vector_retriever=self.vectors_store.as_retriever(
            search_type='similarity',
            search_kwargs=search_kwargs
        )

        bm25_retriever=await self.get_bm25_retriever(user_id=user_id)

        if bm25_retriever:
            weights= await self.get_dynamic_weights(query)
            ensemble_retriever=EnsembleRetriever(
                retrievers=[vector_retriever,bm25_retriever],
                weights=weights
            )
            return ensemble_retriever
        else:
            return vector_retriever

    @staticmethod
    async def get_dynamic_weights(query:str=None):
        default_vector_weights=0.5
        default_bm25_weights=0.5

        if not query:
            return [default_vector_weights,default_bm25_weights]
        
        query_length=len(query)
        query_words=len(query.split())

        if query_length>50:
            vector_weights=0.7
            bm25_weights=0.3
        elif query_length<20:
            vector_weights=0.3
            bm25_weights=0.7
        else:
            vector_weights=0.5
            bm25_weights=0.5
        
        if query_words>0:
            bili=query_words/query_length
            if bili>0.1:
                bm25_weights=min(bm25_weights+0.1,0.7)
                vector_weights=max(bm25_weights-0.1,0.3)
        return [vector_weights,bm25_weights]

    async def check_md5_hex(self,check_md5_for:str)->bool:
        md5_path=get_abstract_path(chroma_config['md5_hex_store'])
        md5_dir=os.path.dirname(md5_path)
        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir,exist_ok=True)
        if not await aio_os.path.exists(md5_path):
            async with aiofiles.open (md5_path,'w',encoding="utf-8") as f:
                pass
            return False
        
        async with aiofiles.open(md5_path,'r',encoding='utf-8') as f:
            async for line in f:
                if line.strip()==check_md5_for:
                    return True
            return False

    async def save_md5_hex(self,md5_hex:str):
        async with aiofiles.open(get_abstract_path(chroma_config['md5_hex_store']),'a',encoding="utf-8") as f:
            await f.write(md5_hex+'\n')

    async def delete_user_documents(self,user_id:str):
        try:
            await asyncio.to_thread(
                self.vectors_store.delete,
                where={"user_id":user_id}
            )
            logger.info(f"【向量库】用户文档已删除 | user={user_id}")
        except Exception as e:
            logger.error(f"【向量库】用户{user_id}的文档删除出现异常{e}")
            raise

    async def delete_all_documents(self):
        """删除向量数据库中所有文档，并清空 MD5 记录"""
        try:
            # 获取所有文档 ID 后删除
            all_ids = await asyncio.to_thread(self.vectors_store.get, include=[])
            if all_ids and all_ids.get("ids"):      
                await asyncio.to_thread(self.vectors_store.delete, ids=all_ids["ids"])
            logger.info("【向量库】所有文档已清空")
        except Exception as e:
            logger.error(f"【向量库】清空所有文档异常 | {e}")
            raise
        try:
            # 清空 MD5 记录文件
            md5_path = get_abstract_path(chroma_config['md5_hex_store'])
            async with aiofiles.open(md5_path, 'w', encoding='utf-8') as f:
                await f.truncate(0)
            logger.info("【向量库】MD5记录已清空")
        except Exception as e:
            logger.error(f"【向量库】清空MD5记录异常 | {e}")

    async def get_file_document(self,read_path:str)-> list[Document]:
        if read_path.endswith(".txt"):
            return await txt_loader(read_path) 
        elif read_path.endswith(".pdf"):
            return await pdf_loader(read_path)
        elif read_path.endswith(".md"):
            return await markdown_loader(read_path)
        elif read_path.endswith(".pptx"):
            return await ppt_loader(read_path)
        elif read_path.endswith(".docx"):
            return await word_loader(read_path)
        else:
            return []

    async def store_document(self,files:list=None,user_id:str=None):
        files_path=[]
        if files:
            for file in files:
                tempfile_path=await asyncio.to_thread(
                    tempfile.NamedTemporaryFile,
                    suffix=file.split('.')[-1],
                    delete=False
                )
                content=await file.read()
                await asyncio.to_thread(tempfile_path.write,content)
                files_path.append(tempfile_path.name)
        else:
            allowed_file_path:tuple(str)=await listdir_allowed_type(
                chroma_config['data_path'],
                tuple(chroma_config['allow_knowledge_file_types'])
            )
            files_path=list(allowed_file_path)
        
        for file_path in files_path:
            md5_hex=await get_file_md5_hex(file_path)
            if await self.check_md5_hex(md5_hex):
                logger.info(f"【向量库】文件已存在，跳过入库 | {file_path}")
                if files:
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                continue

            try:
                documents:list[Document]=await self.get_file_document(file_path)
                if not documents:
                    logger.error(f"向量数据库加载文档{file_path}为空，跳过入库")
                    if files:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                    continue

                # 切分文档
                documents:list[Document] = await self.spliter.split_documents(documents)

                #给分块文档加上分块索引和源头文件名
                for i, doc in enumerate(documents,1):
                    doc.metadata["chunk_index"] = i
                    doc.metadata["source_file"]=os.path.basename(doc.metadata["source"])

                if not documents:
                    logger.error(f"【向量库】文档切分为空，跳过入库 | {file_path}")
                    if files:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            logger.error(f"【向量库】删除临时文件异常 | {file_path} | {e}")
                    continue
                
                #切分用户 user_id 作为元数据
                if user_id:
                    for doc in documents:
                        doc.metadata['user_id']=user_id
                
                await asyncio.to_thread(
                    self.vectors_store.add_documents,
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

    async def delete_by_doc_id(self, doc_id: int) -> int:
        """删除指定 doc_id 的所有向量，返回删除数量"""
        try:
            all_data = await asyncio.to_thread(self.vectors_store.get, include=["metadatas"])
            ids_to_delete = []
            for i, meta in enumerate(all_data.get("metadatas", []) if all_data else []):
                if meta and meta.get("doc_id") == doc_id:
                    ids_to_delete.append(all_data["ids"][i])
            if ids_to_delete:
                await asyncio.to_thread(self.vectors_store.delete, ids=ids_to_delete)
                logger.info(f"【向量库】已删除 doc_id={doc_id} 的 {len(ids_to_delete)} 条向量")
            return len(ids_to_delete)
        except Exception as e:
            logger.error(f"【向量库】删除 doc_id={doc_id} 的向量异常: {e}")
            return 0

    async def delete_by_kb_id(self, kb_id: int) -> int:
        """删除指定 kb_id 的所有向量，返回删除数量"""
        try:
            all_data = await asyncio.to_thread(self.vectors_store.get, include=["metadatas"])
            ids_to_delete = []
            for i, meta in enumerate(all_data.get("metadatas", []) if all_data else []):
                if meta and meta.get("kb_id") == kb_id:
                    ids_to_delete.append(all_data["ids"][i])
            if ids_to_delete:
                await asyncio.to_thread(self.vectors_store.delete, ids=ids_to_delete)
                logger.info(f"【向量库】已删除 kb_id={kb_id} 的 {len(ids_to_delete)} 条向量")
            return len(ids_to_delete)
        except Exception as e:
            logger.error(f"【向量库】删除 kb_id={kb_id} 的向量异常: {e}")
            return 0


# 兼容旧代码的别名
VectorStore = VectorStoreService



                
            


            


                
                
                
            








            



        