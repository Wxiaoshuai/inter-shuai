"""RAG session and message API routers."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body

from src.db.models import RAGSessionModel, RAGMessageModel, RAGDocumentModel
from src.rag.service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG Session"])


@router.post("/sessions")
async def create_session(title: Optional[str] = None) -> dict:
    """Create a new RAG session."""
    try:
        session = await RAGSessionModel.create(title=title)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(limit: int = 50, offset: int = 0) -> dict:
    """List all RAG sessions."""
    try:
        sessions = await RAGSessionModel.get_all(limit=limit, offset=offset)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get a RAG session by ID."""
    try:
        session = await RAGSessionModel.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a RAG session and its messages."""
    try:
        await RAGSessionModel.delete(session_id)
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/messages")
async def create_message(
    session_id: str,
    body: dict = Body(...),
) -> dict:
    """Create a new message in a RAG session."""
    try:
        # Check session exists
        session = await RAGSessionModel.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        role = body.get("role")
        content = body.get("content")
        metadata = body.get("metadata")

        if not role or not content:
            raise HTTPException(status_code=400, detail="role and content are required")

        message = await RAGMessageModel.create(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str) -> dict:
    """Get all messages for a RAG session."""
    try:
        messages = await RAGMessageModel.get_by_session(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}/title")
async def update_session_title(session_id: str, title: str) -> dict:
    """Update a RAG session title."""
    try:
        await RAGSessionModel.update_title(session_id, title)
        return {"status": "success", "session_id": session_id, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/documents")
async def add_session_documents(
    session_id: str,
    body: dict = Body(...),
) -> dict:
    """Add documents to a collection and store metadata."""
    try:
        session = await RAGSessionModel.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        collection = body.get("collection", "default")
        documents = body.get("documents", [])

        if not documents:
            raise HTTPException(status_code=400, detail="documents are required")

        # Store each document in database
        stored_docs = []
        for doc in documents:
            content = doc.get("content")
            metadata = doc.get("metadata", {})
            name = metadata.get("source", f"doc_{len(stored_docs)}")

            stored = await RAGDocumentModel.create(
                collection=collection,
                name=name,
                content=content,
                metadata=metadata,
            )
            stored_docs.append(stored)

        return {"status": "success", "documents": stored_docs}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/create-index")
async def create_index_with_documents(body: dict = Body(...)) -> dict:
    """Create index and store documents in database."""
    try:
        collection = body.get("collection", "default")
        documents = body.get("documents", [])

        if not documents:
            raise HTTPException(status_code=400, detail="documents are required")

        # Store documents in MySQL first
        stored_docs = []
        for doc in documents:
            content = doc.get("content")
            metadata = doc.get("metadata", {})
            name = metadata.get("source", f"doc_{len(stored_docs)}")

            stored = await RAGDocumentModel.create(
                collection=collection,
                name=name,
                content=content,
                metadata=metadata,
            )
            stored_docs.append(stored)

        # Create index in Milvus
        from src.rag.schemas import IndexCreateRequest
        request = IndexCreateRequest(
            documents=documents,
            collection=collection,
            chunk_size=500,
            chunk_overlap=50,
        )
        result = rag_service.create_index(request)

        return {
            "status": "success",
            "documents": stored_docs,
            "index": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))