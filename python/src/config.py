"""Configuration management using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App settings
    app_name: str = "AI RAG & Agent Service"
    debug: bool = False

    # Milvus settings
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "default_collection"

    # MySQL settings
    mysql_host: str = "192.168.1.33"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "ai_memory"

    # LLM settings (DeepSeek)
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding settings (阿里云百炼)
    bailian_api_key: Optional[str] = None
    bailian_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    bailian_embedding_model: str = "text-embedding-3-small"

    # RAG settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    search_k: int = 3

    # Agent settings
    max_iterations: int = 10
    agent_timeout: int = 300

    # Memory settings
    short_term_max_messages: int = 20  # 短期记忆保留消息数
    long_term_memory_enabled: bool = True  # 是否启用长期记忆


settings = Settings()