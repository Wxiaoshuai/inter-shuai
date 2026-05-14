"""Persistence layer for permanent storage."""

from typing import List, Dict, Any, Optional

from src.db.models import AgentModel, ConversationModel, LongTermMemoryModel
from src.memory.short_term import memory_manager
from src.memory.long_term import get_long_term_memory


class PersistenceManager:
    """Manager for permanent storage operations."""

    # ==================== Agent Operations ====================

    @staticmethod
    async def create_agent(
        name: str,
        description: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        """Create a new agent with permanent storage."""
        return await AgentModel.create(
            name=name,
            description=description,
            tools=tools,
            max_iterations=max_iterations,
        )

    @staticmethod
    async def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent from permanent storage."""
        return await AgentModel.get_by_id(agent_id)

    @staticmethod
    async def get_all_agents() -> List[Dict[str, Any]]:
        """Get all agents from permanent storage."""
        return await AgentModel.get_all()

    @staticmethod
    async def update_agent_status(agent_id: str, status: str) -> None:
        """Update agent status in permanent storage."""
        await AgentModel.update_status(agent_id, status)

    @staticmethod
    async def delete_agent(agent_id: str) -> None:
        """Delete agent and all associated data."""
        # Delete short-term memory
        memory_manager.remove(agent_id)

        # Delete conversations
        # Note: This should cascade in DB, but explicit is better
        await AgentModel.delete(agent_id)

    # ==================== Conversation Operations ====================

    @staticmethod
    async def save_conversation(
        agent_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Save a conversation message to permanent storage."""
        return await ConversationModel.create(
            agent_id=agent_id,
            role=role,
            content=content,
            metadata=metadata,
        )

    @staticmethod
    async def get_conversations(
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get conversations from permanent storage."""
        return await ConversationModel.get_by_agent(agent_id, limit, offset)

    @staticmethod
    async def get_recent_conversations(agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversations from permanent storage."""
        return await ConversationModel.get_recent(agent_id, limit)

    @staticmethod
    async def get_conversation_count(agent_id: str) -> int:
        """Get total conversation count for an agent."""
        return await ConversationModel.count(agent_id)

    # ==================== Memory Operations ====================

    @staticmethod
    async def add_long_term_memory(
        agent_id: str,
        content: str,
        memory_type: str = "fact",
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Add a long-term memory."""
        memory = get_long_term_memory(agent_id)
        return await memory.add_memory(content, memory_type, metadata)

    @staticmethod
    async def search_long_term_memory(
        agent_id: str,
        query: str,
        k: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search long-term memories."""
        memory = get_long_term_memory(agent_id)
        return await memory.search(query, k, memory_type)

    @staticmethod
    async def clear_long_term_memory(agent_id: str) -> None:
        """Clear all long-term memories for an agent."""
        memory = get_long_term_memory(agent_id)
        await memory.clear()

    @staticmethod
    async def summarize_and_store(agent_id: str, messages: List[Dict]) -> str:
        """Summarize conversation and store as long-term memory."""
        memory = get_long_term_memory(agent_id)
        return await memory.summarize_conversation(messages)

    # ==================== Short-term Memory Operations ====================

    @staticmethod
    def get_short_term_memory(agent_id: str):
        """Get short-term memory for an agent."""
        return memory_manager.get_or_create(agent_id)

    @staticmethod
    async def persist_short_term_memory(agent_id: str) -> None:
        """Persist short-term memory to permanent storage."""
        memory = memory_manager.get_or_create(agent_id)
        await memory.persist()
        memory.reset_counter()

    @staticmethod
    async def load_short_term_memory(agent_id: str, limit: int = None) -> None:
        """Load short-term memory from permanent storage."""
        memory = memory_manager.get_or_create(agent_id)
        await memory.load_from_db(limit)


# Global persistence manager
persistence = PersistenceManager()