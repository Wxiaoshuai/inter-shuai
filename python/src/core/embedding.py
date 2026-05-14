"""Embedding initialization module."""

from typing import Optional, List
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings

from src.config import settings


def get_embedding(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> OpenAIEmbeddings | DashScopeEmbeddings:
    """
    Get Embedding model instance.

    Args:
        model: Model name
        api_key: API key
        base_url: Base URL

    Returns:
        Embedding model instance
    """
    if model and "dashscope" in model.lower():
        return DashScopeEmbeddings(
            model=model or settings.bailian_embedding_model,
            dashscope_api_key=api_key or settings.bailian_api_key,
        )

    return OpenAIEmbeddings(
        model=model or settings.bailian_embedding_model,
        api_key=api_key or settings.bailian_api_key,
        base_url=base_url or settings.bailian_base_url,
    )


def get_dashscope_embedding(
    model: str = "text-embedding-3-large",
    api_key: Optional[str] = None,
) -> DashScopeEmbeddings:
    """
    Get DashScope Embedding (阿里云百炼) instance.

    Args:
        model: Model name (default: text-embedding-3-large)
        api_key: API key

    Returns:
        DashScopeEmbeddings instance
    """
    return DashScopeEmbeddings(
        model=model,
        dashscope_api_key=api_key or settings.bailian_api_key,
    )


# Default embedding instance
default_embedding = get_dashscope_embedding()