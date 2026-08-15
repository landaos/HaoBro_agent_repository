from abc import ABC,abstractmethod
from typing import Union

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import BaseDocumentCompressor
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_compressors.dashscope_rerank import DashScopeRerank
from src.config import settings

class BaseModelFactory(ABC):
    @abstractmethod
    def create_model(self) -> Union[BaseChatModel, Embeddings, BaseDocumentCompressor]:
        """创建模型实例"""
        pass

class ClatModelFactory(BaseModelFactory):
    def create_model(self) -> BaseChatModel:
        """创建聊天模型实例"""
        return ChatTongyi(
            model_name=settings.chat_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            streaming=True,
            top_p=0.3,
        )


class LocalEmbedModelFactory(BaseModelFactory):
    def create_model(self) -> Embeddings:
        """创建嵌入模型实例"""
        return  DashScopeEmbeddings(
            model=settings.vector_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
        )


class RerankerModelFactory(BaseModelFactory):
    def create_model(self) ->BaseDocumentCompressor:
        reranker = DashScopeRerank(
            model=settings.reranker_model_name,
            dashscope_api_key=settings.ali_access_key_secret,
            top_n=5,   
        )
        reranker.model = settings.reranker_model_name  # 覆盖 langchain 硬编码的 'gte-rerank'
        return reranker

chat_model=ClatModelFactory().create_model()
embed_model=LocalEmbedModelFactory().create_model()
reranker_model=RerankerModelFactory().create_model()
