import sys
import asyncio
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.logger.logger import logger
from src.core.agent.factory import chat_model
from src.core.rag.reranker import CloudReranker
from src.core.rag.vector_store import VectorStoreService
from langchain_community.chat_models.tongyi import ChatTongyi
from src.config import settings
from src.prompt.prompt_loader import load_prompt                                
            

class ragService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.reranker = CloudReranker()
        self.chat_model = chat_model
        self.text=load_prompt("rag_summarize_prompt")
        self.prompt_template = PromptTemplate.from_template(self.text)
        self.hyde_prompt_template = PromptTemplate.from_template("请根据以下问题生成一个假设性文档，我会根据你生成的假设性文档去向量数据库去检索文件,\n\n问题：{query}\n\n,假设性回答:")
        self.chain=self._init_chain()

    def _init_chain(self):
        return self.prompt_template | self.chat_model | StrOutputParser() 

    async def generate_hypothetical_document(self,query:str)->str:
        try:
            logger.info("【hyde】开始生成假设性文档")
            hyde_model = ChatTongyi(
            model_name=settings.chat_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            streaming=True,
            top_p=0.7,
            )
            hyde_chain = self.hyde_prompt_template | hyde_model | StrOutputParser() 
            hyde_document=await hyde_chain.ainvoke({"query":query})
            logger.info(f"【hyde】成功生成假设性文档: {hyde_document}")
            return hyde_document
        except Exception as e:
            logger.error(f"【hyde】生成假设性文档失败: {e}")
            return query

    async def retriever_documents(self,query:str,user_id:str|None=None):
        try:
            retriever = await self.vector_store.get_retriever(query, user_id)
            logger.info("【rag】开始检索文档")
            hyde_document=await self.generate_hypothetical_document(query)
            documents=await retriever.ainvoke(hyde_document)
            logger.info(f"【rag】检索到{len(documents)}条文档")
            return documents
        except Exception as e:
            logger.error(f"【rag】检索文档失败: {e}")
            return []

    async def reranker_documents(self,query:str,documents_filtered:list,documents:list)->list:
        try:
            logger.info("【rag】开始对文档进行重排序")
            rerankered_documents=await self.reranker.get_reranker_documents(query, documents_filtered, documents)
            logger.info(f"【rag】成功对{len(documents)}条文档进行重排序,且得到了{len(rerankered_documents)}条文档")
            return rerankered_documents
        except Exception as e:
            logger.error(f"【rag】对文档进行重排序失败: {e}")
            return documents

    async def rag_core(self,query:str,user_id:str|None=None)->str:
        try:
            documents=await self.retriever_documents(query,user_id)
            documents_filtered=[doc.page_content for doc in documents]
            documents_rerankered=await self.reranker_documents(query,documents_filtered,documents)
            if not documents_rerankered:
                return "未检索到相关文档,请直接回答问题,并说明未检索到相关文档"
            max_score=max([doc["relevance_score"] for doc in documents_rerankered])
            for i,score in enumerate([doc["relevance_score"] for doc in documents_rerankered], 1):
                logger.info(f"【rag】文档{i}的相似度: {score}")
            for i,doc in enumerate([doc["document"] for doc in documents_rerankered],1):
                logger.info(f"【rag】文档{i}的内容: {doc}\n")
            if max_score>0.55:
                final_document=""
                logger.info("【rag】最相关文档相似度大于0.55,使用rag链路生成回答")
                reranked_documents=[doc["document"] for doc in documents_rerankered if doc["relevance_score"]>0.5]
                logger.info(f"【rag】最终基于{len(reranked_documents)}条检索文档进行用户问题解答")
                for i,doc in enumerate(reranked_documents,1):
                    final_document+=f"{doc}\n"
                import time
                start_time=time.time()
                try:
                    final_answer= await asyncio.wait_for(self.chain.ainvoke({"query":query,"context":final_document}),timeout=30)
                except asyncio.TimeoutError:
                    return "rag链路生成最终回答超时,请稍后重试"
                end_time=time.time()
                logger.info(f"【rag】生成最终回答耗时: {end_time-start_time:.2f}秒")
                logger.info(f"【rag】成功生成最终回答: {final_answer}")
                return final_answer
            else:
                logger.info("【rag】最相关文档相似度小于0.55,放弃调用rag链路,让大语言模型自已生成最终回答")
                final_answer="rag链路最相关文档相似度小于0.55,未生成rag回答,请你自已生成最终回答,并说明未生成rag回答的原因"
                return final_answer
        except Exception as e:
            logger.error(f"【rag】rag_core失败: {e}")
            return "rag链路生成最终回答失败,请稍后重试"

if __name__ == '__main__':
    async def main():
        rag_service=ragService()
        await rag_service.vector_store.delete_all_documents()
        # await rag_service.vector_store.store_document()
        # query="你好,推荐哪一款扫地机器人"
        # answer=await rag_service.rag_core(query)
        # logger.info("--------------------以下是最终回答---------------------")
        # logger.info(f"【rag】最终回答: {answer}")
    
    asyncio.run(main())
        


    
    

    
        
    



    