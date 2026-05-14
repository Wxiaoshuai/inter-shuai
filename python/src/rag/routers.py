"""RAG API routers."""

from fastapi import APIRouter, HTTPException

from src.rag.service import rag_service
from src.rag.schemas import (
    IndexCreateRequest,
    IndexAddRequest,
    SearchRequest,
    SearchResponse,
    AskRequest,
    AskResponse,
    CollectionListResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/index/create")
async def create_index(request: IndexCreateRequest) -> dict:
    """Create a new index with documents."""
    try:
        result = rag_service.create_index(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/{collection}")
async def add_to_index(collection: str, request: IndexAddRequest) -> dict:
    """Add documents to existing index."""
    try:
        result = rag_service.add_documents(collection, request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/{collection}")
async def delete_index(collection: str) -> dict:
    """Delete an index."""
    try:
        result = rag_service.delete_index(collection)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    """Perform similarity search."""
    try:
        result = rag_service.search(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask(request: AskRequest) -> AskResponse:
    """Ask a question with RAG context."""
    try:
        result = rag_service.ask(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def list_collections() -> CollectionListResponse:
    """List all collections."""
    try:
        result = rag_service.list_collections()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))