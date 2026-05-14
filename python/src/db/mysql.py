"""MySQL connection pool management."""

import aiomysql
from typing import Optional
from contextlib import asynccontextmanager

from src.config import settings


class MySQLPool:
    """MySQL connection pool manager."""

    _pool: Optional[aiomysql.Pool] = None

    @classmethod
    async def get_pool(cls) -> aiomysql.Pool:
        """Get or create connection pool."""
        if cls._pool is None:
            cls._pool = await aiomysql.create_pool(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                db=settings.mysql_database,
                autocommit=True,
                minsize=5,
                maxsize=20,
                charset='utf8mb4',
            )
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close connection pool."""
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get a connection from pool."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn

    @classmethod
    @asynccontextmanager
    async def get_cursor(cls):
        """Get a cursor from pool."""
        async with cls.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                yield cursor


async def init_database():
    """Initialize database and create tables."""
    pool = await MySQLPool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Create database if not exists
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            await cursor.execute(f"USE {settings.mysql_database}")

            # Create agents table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    tools JSON,
                    max_iterations INT DEFAULT 10,
                    status VARCHAR(20) DEFAULT 'ready',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            # Create conversations table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(36) PRIMARY KEY,
                    agent_id VARCHAR(36) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_conversation_agent (agent_id),
                    INDEX idx_conversation_created (created_at)
                )
            """)

            # Create long_term_memory table (SQL fallback for when Milvus unavailable)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id VARCHAR(36) PRIMARY KEY,
                    agent_id VARCHAR(36) NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    vector JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_memory_agent (agent_id),
                    INDEX idx_memory_type (memory_type)
                )
            """)

            # Create rag_sessions table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_rag_session_updated (updated_at)
                )
            """)

            # Create rag_messages table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_messages (
                    id VARCHAR(36) PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_rag_msg_session (session_id),
                    INDEX idx_rag_msg_created (created_at)
                )
            """)

            # Create rag_documents table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id VARCHAR(36) PRIMARY KEY,
                    collection VARCHAR(100) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_rag_doc_collection (collection),
                    INDEX idx_rag_doc_created (created_at)
                )
            """)

    print(f"✅ Database {settings.mysql_database} initialized")


mysql_pool = MySQLPool()