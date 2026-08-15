import math
import asyncio
from typing import List,Optional,Any
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.configs.config_loader import chroma_config

class AsyncTextSplitter:
    def __init__(self,
     chunk_size: int = chroma_config['chunk_size'],
     chunk_overlap: int = chroma_config['chunk_overlap'],
     separators: Optional[List[str]] = None,
     embedding_model: Optional[Embeddings]=None):
        default_separators = chroma_config['separators']

        self.embedding_model = embedding_model
        self.separators =  separators or default_separators
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
    
    async def split_text(self,text:str)->List[str]:
        chunks= await asyncio.to_thread(self.splitter.split_text,text)
        if self.embedding_model:
            chunks=await self.more_split(chunks)
        return chunks
    
    async def split_documents(self,documents:List[Any])->List[Any]:
        return await asyncio.to_thread(self.splitter.split_documents,documents)

    
    async def more_split(self,chunks:List[str])->List[str]:
        more_chunks=[]
        current_chunk=chunks[0]
        for i in range(1,len(chunks)):
            similarity=await self.get_similarity(current_chunk,chunks[i])
            if similarity>0.7:
                current_chunk+=" "+chunks[i]
            else:
                more_chunks.append(current_chunk)
                current_chunk=chunks[i]

        more_chunks.append(current_chunk)
        return more_chunks
    
    async def get_similarity(self,chunk1:str,chunk2:str)->float:
        if not self.embedding_model:
            return 0.0
        embedding1 = await asyncio.to_thread(self.embedding_model.embed_query,chunk1)
        embedding2 = await asyncio.to_thread(self.embedding_model.embed_query,chunk2)
        
        similarity = await asyncio.to_thread(self.calculate_similarity,embedding1,embedding2)
        return similarity
    
    def calculate_similarity(self,embedding1:List[float],embedding2:List[float])->float:
        import math
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a**2 for a in embedding1))
        magnitude2 = math.sqrt(sum(b**2 for b in embedding2))
        if magnitude1 * magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
      
         

    

