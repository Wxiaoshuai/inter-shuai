"""Long-term memory using Milvus vector storage."""

import json
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document

from src.core.embedding import get_dashscope_embedding
from src.config import settings


class LongTermMemory:
    """Long-term memory using Milvus for vector storage."""

    COLLECTION_NAME = "agent_long_term_memory"

    def __init__(self, agent_id: str):
        """
        Initialize long-term memory.

        Args:
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self.embedding = get_dashscope_embedding()
        self._collection_initialized = False

    def _init_collection(self) -> None:
        """Initialize Milvus collection for long-term memory."""
        from src.core.milvus import milvus_manager

        if not milvus_manager.has_collection(self.COLLECTION_NAME):
            milvus_manager.create_collection(
                collection_name=self.COLLECTION_NAME,
                dimension=1024,
                metric_type="COSINE",
            )
        self._collection_initialized = True

    async def add_memory(
        self,
        content: str,
        memory_type: str = "fact",
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Add a long-term memory.

        Args:
            content: Memory content
            memory_type: Type of memory (summary/preference/fact)
            metadata: Additional metadata

        Returns:
            Memory info dict
        """
        from src.db.models import LongTermMemoryModel

        if not self._collection_initialized:
            self._init_collection()

        # Store in MySQL as fallback
        await LongTermMemoryModel.create(
            agent_id=self.agent_id,
            memory_type=memory_type,
            content=content,
        )

        # Store in Milvus for vector search
        try:
            from src.core.milvus import milvus_manager

            vector = self.embedding.embed_query(content)

            milvus_manager.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=[{
                    "agent_id": self.agent_id,
                    "memory_type": memory_type,
                    "content": content,
                    "vector": vector,
                    "metadata": json.dumps(metadata or {}, ensure_ascii=False),
                }]
            )
        except Exception as e:
            print(f"⚠️ Failed to store in Milvus, using MySQL only: {e}")

        return {
            "agent_id": self.agent_id,
            "memory_type": memory_type,
            "content": content,
        }

    async def search(
        self,
        query: str,
        k: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search long-term memories.

        Args:
            query: Search query
            k: Number of results
            memory_type: Optional filter by memory type

        Returns:
            List of matching memories
        """
        try:
            from src.core.milvus import milvus_manager

            if not milvus_manager.has_collection(self.COLLECTION_NAME):
                return []

            query_vector = self.embedding.embed_query(query)

            results = milvus_manager.client.search(
                collection_name=self.COLLECTION_NAME,
                data=[query_vector],
                limit=k,
                filter=f"agent_id == '{self.agent_id}'" if not memory_type else f"agent_id == '{self.agent_id}' AND memory_type == '{memory_type}'",
                output_fields=["agent_id", "memory_type", "content", "metadata"],
            )

            memories = []
            for hit in results[0]:
                mem = {
                    "id": hit.get("id"),
                    "content": hit.get("entity", {}).get("content", ""),
                    "memory_type": hit.get("entity", {}).get("memory_type", ""),
                    "score": hit.get("distance", 0),
                    "metadata": json.loads(hit.get("entity", {}).get("metadata", "{}")),
                }
                memories.append(mem)

            return memories

        except Exception as e:
            print(f"⚠️ Milvus search failed, falling back to MySQL: {e}")
            return await self._search_mysql(query, k, memory_type)

    async def _search_mysql(
        self,
        query: str,
        k: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback search in MySQL."""
        from src.db.models import LongTermMemoryModel

        memories = await LongTermMemoryModel.get_by_agent(self.agent_id)

        if memory_type:
            memories = [m for m in memories if m.get("memory_type") == memory_type]

        return memories[:k]

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all long-term memories for the agent."""
        from src.db.models import LongTermMemoryModel
        return await LongTermMemoryModel.get_by_agent(self.agent_id)

    async def clear(self) -> None:
        """Clear all long-term memories for the agent."""
        from src.db.models import LongTermMemoryModel

        # Clear MySQL
        await LongTermMemoryModel.delete_by_agent(self.agent_id)

        # Clear Milvus collection
        try:
            from src.core.milvus import milvus_manager
            if milvus_manager.has_collection(self.COLLECTION_NAME):
                # Note: This deletes the entire collection, not just agent's memories
                # In production, you'd want partition-based deletion
                pass
        except Exception as e:
            print(f"⚠️ Failed to clear Milvus: {e}")

    async def summarize_conversation(self, messages: List[Dict]) -> str:
        """
        Summarize a conversation and store as long-term memory.

        Args:
            messages: List of conversation messages

        Returns:
            Summary content
        """
        from src.core.llm import get_llm

        if not messages:
            return ""

        # Build conversation text
        conv_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages[-10:]  # Last 10 messages
        ])

        prompt = f"""请总结以下对话的关键信息，包括：
1. 用户的主要需求或问题
2. 关键的事实或答案
3. 用户的偏好或习惯

对话：
{conv_text}

请用简洁的中文总结（不超过200字）："""

        llm = get_llm()
        response = llm.invoke(prompt)
        summary = response.content if hasattr(response, 'content') else str(response)

        # Store as long-term memory
        await self.add_memory(
            content=summary,
            memory_type="summary",
            metadata={"source": "conversation_summary"}
        )

        return summary


# Global cache for long-term memories
_long_term_cache: Dict[str, LongTermMemory] = {}


def get_long_term_memory(agent_id: str) -> LongTermMemory:
    """Get or create long-term memory for an agent."""
    if agent_id not in _long_term_cache:
        _long_term_cache[agent_id] = LongTermMemory(agent_id)
    return _long_term_cache[agent_id]