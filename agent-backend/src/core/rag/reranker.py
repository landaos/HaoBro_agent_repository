from typing import List, Dict, Any
from src.config import settings
from src.core.agent.factory import reranker_model
from src.logger.logger import logger
import asyncio

class CloudReranker:
    def __init__(self):
        self.reranker = reranker_model
        
    async def get_reranker_documents(self, query:str,documents_filtered: List[str],documents: List[Any]) -> List[Dict[str, Any]]:
        """对文档进行重排序"""
        if not documents_filtered:
            return []
        try:
            results = await asyncio.to_thread(self.reranker.rerank, documents_filtered, query)
            # DashScopeRerank 只返回 index 和 relevance_score，需手动补回文档内容
            for item in results:
                idx = item["index"]
                if idx < len(documents_filtered):
                    item["document"] ="【参考文件来源:"+documents[idx].metadata.get("source_file","未知文件")+"第"+str(documents[idx].metadata.get('chunk_index',"?"))+"分块】\n"+documents_filtered[idx]
            return results  
        except Exception as e:
            logger.error(f"【reranker】文档云端重排序失败 | {e}")
            return []

