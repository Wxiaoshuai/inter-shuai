"""RAG module Pydantic schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document model for indexing."""
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Document metadata")


class IndexCreateRequest(BaseModel):
    """Request to create a new index."""
    documents: List[Document] = Field(..., description="Documents to index")
    collection: str = Field(..., description="Collection name")
    chunk_size: Optional[int] = Field(500, description="Chunk size for splitting")
    chunk_overlap: Optional[int] = Field(50, description="Chunk overlap")


class IndexAddRequest(BaseModel):
    """Request to add documents to existing index."""
    documents: List[Document] = Field(..., description="Documents to add")
    chunk_size: Optional[int] = Field(500, description="Chunk size for splitting")
    chunk_overlap: Optional[int] = Field(50, description="Chunk overlap")


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., description="Search query")
    k: Optional[int] = Field(3, description="Number of results to return")
    collection: str = Field(..., description="Collection name")


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Search response."""
    results: List[SearchResult]
    query: str


class AskRequest(BaseModel):
    """RAG ask request."""
    question: str = Field(..., description="Question to ask")
    collection: str = Field(..., description="Collection name")
    k: Optional[int] = Field(3, description="Number of context documents")


class AskResponse(BaseModel):
    """RAG ask response."""
    answer: str
    sources: List[str]
    context: List[SearchResult]


class CollectionInfo(BaseModel):
    """Collection information."""
    name: str
    row_count: int
    dimension: Optional[int] = None


class CollectionListResponse(BaseModel):
    """Collection list response."""
    collections: List[CollectionInfo]