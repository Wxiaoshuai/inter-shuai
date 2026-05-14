"""RAG service layer."""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from src.rag.tools import RAGTools
from src.rag.schemas import (
    IndexCreateRequest,
    IndexAddRequest,
    SearchRequest,
    SearchResponse,
    SearchResult,
    AskRequest,
    AskResponse,
    CollectionInfo,
    CollectionListResponse,
)
from src.core.llm import get_llm
from src.core.milvus import milvus_manager
from src.config import settings


class RAGService:
    """RAG service for document indexing and问答."""

    def __init__(self):
        self._tools: Dict[str, RAGTools] = {}
        self._llm = get_llm()

    def get_or_create_tools(self, collection: str) -> RAGTools:
        """Get or create RAG tools for a collection."""
        if collection not in self._tools:
            self._tools[collection] = RAGTools(
                collection_name=collection,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        return self._tools[collection]

    def create_index(self, request: IndexCreateRequest) -> dict:
        """
        Create a new index with documents.

        Args:
            request: Index create request

        Returns:
            Result dict with status
        """
        tools = self.get_or_create_tools(request.collection)

        docs = tools.load_documents(request.documents)
        chunks = tools.split_documents(
            docs,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        tools.create_vector_store(chunks)

        return {
            "status": "success",
            "collection": request.collection,
            "chunks_created": len(chunks),
        }

    def add_documents(self, collection: str, request: IndexAddRequest) -> dict:
        """
        Add documents to existing index.

        Args:
            collection: Collection name
            request: Add documents request

        Returns:
            Result dict with status
        """
        tools = self.get_or_create_tools(collection)

        docs = tools.load_documents(request.documents)
        chunks = tools.split_documents(
            docs,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        tools.add_to_vector_store(chunks)

        return {
            "status": "success",
            "collection": collection,
            "chunks_added": len(chunks),
        }

    def delete_index(self, collection: str) -> dict:
        """Delete an index."""
        if collection in self._tools:
            del self._tools[collection]

        if milvus_manager.has_collection(collection):
            milvus_manager.drop_collection(collection)

        return {"status": "success", "collection": collection}

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform similarity search.

        Args:
            request: Search request

        Returns:
            Search response with results
        """
        tools = self.get_or_create_tools(request.collection)

        results = tools.similarity_search(request.query, k=request.k)

        search_results = [
            SearchResult(
                id=r["id"],
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ]

        return SearchResponse(results=search_results, query=request.query)

    def ask(self, request: AskRequest) -> AskResponse:
        """
        Ask a question with RAG context.

        Args:
            request: Ask request

        Returns:
            Ask response with answer and sources
        """
        tools = self.get_or_create_tools(request.collection)

        docs = tools.similarity_search(request.question, k=request.k)

        if not docs:
            # No context found - still provide helpful response
            prompt = f"""你是一个友好的 AI 助手。用户在询问：{request.question}

请给出一个有帮助的回答，可以：
1. 解释相关概念
2. 询问用户是否需要上传文档来获取更准确的答案

回答要简洁、准确，使用中文。"""

            answer = self._llm.invoke(prompt)

            return AskResponse(
                answer=answer.content if hasattr(answer, 'content') else str(answer),
                sources=[],
                context=[],
            )

        context = "\n\n".join([d["content"] for d in docs])

        prompt = f"""你是一个友好的 AI 助手。请根据用户提供的文档内容，准确回答问题。

文档内容：
{context}

问题：{request.question}

回答要求：
1. 如果文档中有相关信息，请说"根据您提供的文档"然后基于文档内容回答
2. 如果文档中没有相关信息，请诚实地说"根据您提供的文档，无法回答这个问题"
3. 如果只是简单的问候，可以不基于文档，用AI生成回复内容
3. 回答要简洁、准确，使用中文

回答："""

        answer = self._llm.invoke(prompt)

        sources = [d["metadata"].get("source", "未知") for d in docs]

        search_results = [
            SearchResult(
                id=d["id"],
                content=d["content"],
                score=d["score"],
                metadata=d["metadata"],
            )
            for d in docs
        ]

        return AskResponse(
            answer=answer.content if hasattr(answer, 'content') else str(answer),
            sources=sources,
            context=search_results,
        )

    def list_collections(self) -> CollectionListResponse:
        """List all collections."""
        collections = milvus_manager.list_collections()

        collection_infos = []
        for name in collections:
            try:
                stats = milvus_manager.get_collection_stats(name)
                collection_infos.append(
                    CollectionInfo(
                        name=name,
                        row_count=stats.get("row_count", 0),
                        dimension=stats.get("dimension"),
                    )
                )
            except Exception:
                collection_infos.append(CollectionInfo(name=name, row_count=0))

        return CollectionListResponse(collections=collection_infos)


# Global service instance
rag_service = RAGService()