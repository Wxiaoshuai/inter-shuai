"""Data models and DAO for database operations."""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.db.mysql import MySQLPool


class AgentModel:
    """Agent data access object."""

    @staticmethod
    async def create(
        name: str,
        description: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        """Create a new agent."""
        agent_id = str(uuid.uuid4())
        tools_json = json.dumps(tools or [], ensure_ascii=False)

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO agents (id, name, description, tools, max_iterations, status)
                VALUES (%s, %s, %s, %s, %s, 'ready')
                """,
                (agent_id, name, description, tools_json, max_iterations),
            )

        return {
            "id": agent_id,
            "name": name,
            "description": description,
            "tools": tools or [],
            "max_iterations": max_iterations,
            "status": "ready",
        }

    @staticmethod
    async def get_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM agents WHERE id = %s", (agent_id,)
            )
            row = await cursor.fetchone()

        if row:
            row["tools"] = json.loads(row["tools"]) if row.get("tools") else []
        return row

    @staticmethod
    async def get_all() -> List[Dict[str, Any]]:
        """Get all agents."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute("SELECT * FROM agents ORDER BY create_at DESC")
            rows = await cursor.fetchall()

        for row in rows:
            row["tools"] = json.loads(row["tools"]) if row.get("tools") else []
        return rows

    @staticmethod
    async def update_status(agent_id: str, status: str) -> None:
        """Update agent status."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "UPDATE agents SET status = %s WHERE id = %s",
                (status, agent_id),
            )

    @staticmethod
    async def delete(agent_id: str) -> None:
        """Delete an agent and its conversations."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "DELETE FROM agents WHERE id = %s", (agent_id,)
            )


class ConversationModel:
    """Conversation data access object."""

    @staticmethod
    async def create(
        agent_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation message."""
        conv_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO conversations (id, agent_id, role, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (conv_id, agent_id, role, content, metadata_json),
            )

        return {
            "id": conv_id,
            "agent_id": agent_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

    @staticmethod
    async def get_by_agent(
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get conversations for an agent."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM conversations
                WHERE agent_id = %s
                ORDER BY create_at DESC
                LIMIT %s OFFSET %s
                """,
                (agent_id, limit, offset),
            )
            rows = await cursor.fetchall()

        for row in rows:
            row["metadata"] = json.loads(row["metadata"]) if row.get("metadata") else {}
        return rows

    @staticmethod
    async def get_recent(agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversations for an agent."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM conversations
                WHERE agent_id = %s
                ORDER BY create_at DESC
                LIMIT %s
                """,
                (agent_id, limit),
            )
            rows = await cursor.fetchall()

        for row in rows:
            row["metadata"] = json.loads(row["metadata"]) if row.get("metadata") else {}
        return list(reversed(rows))

    @staticmethod
    async def count(agent_id: str) -> int:
        """Count conversations for an agent."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) as cnt FROM conversations WHERE agent_id = %s",
                (agent_id,),
            )
            row = await cursor.fetchone()
        return row["cnt"] if row else 0


class RAGSessionModel:
    """RAG chat session data access object."""

    @staticmethod
    async def create(title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new RAG session."""
        session_id = str(uuid.uuid4())
        title = title or f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO rag_sessions (id, title)
                VALUES (%s, %s)
                """,
                (session_id, title),
            )

        return {
            "id": session_id,
            "title": title,
        }

    @staticmethod
    async def get_by_id(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM rag_sessions WHERE id = %s", (session_id,)
            )
            return await cursor.fetchone()

    @staticmethod
    async def get_all(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all sessions ordered by update time."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM rag_sessions
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            return await cursor.fetchall()

    @staticmethod
    async def update_title(session_id: str, title: str) -> None:
        """Update session title."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "UPDATE rag_sessions SET title = %s WHERE id = %s",
                (title, session_id),
            )

    @staticmethod
    async def delete(session_id: str) -> None:
        """Delete a session and its messages."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "DELETE FROM rag_messages WHERE session_id = %s", (session_id,)
            )
            await cursor.execute(
                "DELETE FROM rag_sessions WHERE id = %s", (session_id,)
            )


class RAGMessageModel:
    """RAG chat message data access object."""

    @staticmethod
    async def create(
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a new RAG message."""
        msg_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO rag_messages (id, session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (msg_id, session_id, role, content, metadata_json),
            )
            # Update session's updated_at
            await cursor.execute(
                "UPDATE rag_sessions SET updated_at = NOW() WHERE id = %s",
                (session_id,),
            )

        return {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

    @staticmethod
    async def get_by_session(session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM rag_messages
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()

        for row in rows:
            row["metadata"] = json.loads(row["metadata"]) if row.get("metadata") else {}
        return rows

    @staticmethod
    async def count_by_session(session_id: str) -> int:
        """Count messages for a session."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) as cnt FROM rag_messages WHERE session_id = %s",
                (session_id,),
            )
            row = await cursor.fetchone()
        return row["cnt"] if row else 0


class RAGDocumentModel:
    """RAG document data access object."""

    @staticmethod
    async def create(
        collection: str,
        name: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a new RAG document."""
        doc_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO rag_documents (id, collection, name, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (doc_id, collection, name, content, metadata_json),
            )

        return {
            "id": doc_id,
            "collection": collection,
            "name": name,
            "content": content,
            "metadata": metadata or {},
        }

    @staticmethod
    async def get_by_collection(collection: str) -> List[Dict[str, Any]]:
        """Get all documents for a collection."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM rag_documents
                WHERE collection = %s
                ORDER BY created_at DESC
                """,
                (collection,),
            )
            rows = await cursor.fetchall()

        for row in rows:
            row["metadata"] = json.loads(row["metadata"]) if row.get("metadata") else {}
        return rows

    @staticmethod
    async def get_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM rag_documents WHERE id = %s", (doc_id,)
            )
            row = await cursor.fetchone()

        if row:
            row["metadata"] = json.loads(row["metadata"]) if row.get("metadata") else {}
        return row

    @staticmethod
    async def delete(doc_id: str) -> Dict[str, Any]:
        """Delete a document and return its collection."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM rag_documents WHERE id = %s", (doc_id,)
            )
            row = await cursor.fetchone()

            if not row:
                raise ValueError(f"Document {doc_id} not found")

            await cursor.execute(
                "DELETE FROM rag_documents WHERE id = %s", (doc_id,)
            )

            return {
                "id": doc_id,
                "collection": row["collection"],
                "name": row["name"],
            }

    @staticmethod
    async def delete_by_collection(collection: str) -> int:
        """Delete all documents for a collection."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) as cnt FROM rag_documents WHERE collection = %s",
                (collection,),
            )
            row = await cursor.fetchone()
            count = row["cnt"] if row else 0

            await cursor.execute(
                "DELETE FROM rag_documents WHERE collection = %s", (collection,)
            )

        return count


class LongTermMemoryModel:
    """Long term memory data access object (SQL fallback)."""

    @staticmethod
    async def create(
        agent_id: str,
        memory_type: str,
        content: str,
        vector: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Create a long term memory entry."""
        mem_id = str(uuid.uuid4())
        vector_json = json.dumps(vector, ensure_ascii=False) if vector else None

        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO long_term_memory (id, agent_id, memory_type, content, vector)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (mem_id, agent_id, memory_type, content, vector_json),
            )

        return {
            "id": mem_id,
            "agent_id": agent_id,
            "memory_type": memory_type,
            "content": content,
        }

    @staticmethod
    async def get_by_agent(agent_id: str) -> List[Dict[str, Any]]:
        """Get all long term memories for an agent."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM long_term_memory
                WHERE agent_id = %s
                ORDER BY create_at DESC
                """,
                (agent_id,),
            )
            rows = await cursor.fetchall()

        for row in rows:
            if row.get("vector"):
                row["vector"] = json.loads(row["vector"])
        return rows

    @staticmethod
    async def delete_by_agent(agent_id: str) -> None:
        """Delete all long term memories for an agent."""
        async with MySQLPool.get_cursor() as cursor:
            await cursor.execute(
                "DELETE FROM long_term_memory WHERE agent_id = %s",
                (agent_id,),
            )