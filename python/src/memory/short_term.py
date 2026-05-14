"""Short-term memory management with periodic persistence."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

from src.config import settings
from src.db.models import ConversationModel


class ShortTermMemory:
    """Short-term memory manager with in-memory buffer and periodic persistence."""

    def __init__(self, agent_id: str, max_messages: int = None):
        """
        Initialize short-term memory.

        Args:
            agent_id: Agent identifier
            max_messages: Maximum messages to keep in memory
        """
        self.agent_id = agent_id
        self.max_messages = max_messages or settings.short_term_max_messages
        self._buffer: deque = deque(maxlen=self.max_messages)
        self._persist_interval = 10  # 持久化间隔（消息数）
        self._counter = 0

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to short-term memory."""
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._buffer.append(message)
        self._counter += 1

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from short-term memory."""
        return list(self._buffer)

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get N most recent messages."""
        messages = list(self._buffer)
        return messages[-n:] if len(messages) > n else messages

    def clear(self) -> None:
        """Clear short-term memory."""
        self._buffer.clear()
        self._counter = 0

    async def persist(self) -> None:
        """Persist short-term memory to database."""
        if not self._buffer:
            return

        for message in self._buffer:
            await ConversationModel.create(
                agent_id=self.agent_id,
                role=message["role"],
                content=message["content"],
                metadata=message.get("metadata"),
            )

        print(f"💾 Persisted {len(self._buffer)} messages for agent {self.agent_id}")

    async def load_from_db(self, limit: int = None) -> None:
        """Load recent messages from database."""
        limit = limit or self.max_messages
        messages = await ConversationModel.get_recent(self.agent_id, limit)

        self._buffer.clear()
        for msg in messages:
            self._buffer.append({
                "role": msg["role"],
                "content": msg["content"],
                "metadata": msg.get("metadata", {}),
                "timestamp": msg.get("created_at", "").isoformat() if msg.get("created_at") else "",
            })

        print(f"📥 Loaded {len(self._buffer)} messages from DB for agent {self.agent_id}")

    def should_persist(self) -> bool:
        """Check if should trigger persistence."""
        return self._counter >= self._persist_interval

    def reset_counter(self) -> None:
        """Reset persistence counter."""
        self._counter = 0


class ShortTermMemoryManager:
    """Manager for multiple short-term memories."""

    def __init__(self):
        self._memories: Dict[str, ShortTermMemory] = {}

    def get_or_create(self, agent_id: str) -> ShortTermMemory:
        """Get or create short-term memory for an agent."""
        if agent_id not in self._memories:
            self._memories[agent_id] = ShortTermMemory(agent_id)
        return self._memories[agent_id]

    async def persist_all(self) -> None:
        """Persist all short-term memories."""
        for memory in self._memories.values():
            await memory.persist()
            memory.reset_counter()

    def remove(self, agent_id: str) -> None:
        """Remove short-term memory for an agent."""
        if agent_id in self._memories:
            del self._memories[agent_id]


# Global manager
memory_manager = ShortTermMemoryManager()