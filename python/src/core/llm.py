"""LLM initialization module."""

from typing import Optional
from langchain_openai import ChatOpenAI

from src.config import settings


def get_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
) -> ChatOpenAI:
    """
    Get LLM instance with configuration.

    Args:
        model: Model name (defaults to deepseek-chat)
        api_key: API key (defaults to from settings)
        base_url: Base URL (defaults to from settings)
        temperature: Temperature for generation

    Returns:
        ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model or settings.deepseek_model,
        api_key=api_key or settings.deepseek_api_key,
        base_url=base_url or settings.deepseek_base_url,
        temperature=temperature,
    )


# Default LLM instance
default_llm = get_llm()