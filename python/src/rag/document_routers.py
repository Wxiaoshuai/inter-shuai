"""RAG document API routers."""

from typing import List
from fastapi import APIRouter, HTTPException

from src.db.models import RAGDocumentModel
from src.rag.service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG Document"])


@router.get("/documents")
async def list_documents(collection: str) -> dict:
    """List all documents for a collection."""
    try:
        documents = await RAGDocumentModel.get_by_collection(collection)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict:
    """Delete a document and its associated index entry."""
    try:
        doc_info = await RAGDocumentModel.delete(doc_id)

        # Check if there are remaining documents in the collection
        remaining = await RAGDocumentModel.get_by_collection(doc_info["collection"])
        if not remaining:
            # No more documents, delete the index
            rag_service.delete_index(doc_info["collection"])

        return {
            "status": "success",
            "doc_id": doc_id,
            "collection": doc_info["collection"],
            "name": doc_info["name"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection}")
async def delete_collection(collection: str) -> dict:
    """Delete a collection and all its documents."""
    try:
        count = await RAGDocumentModel.delete_by_collection(collection)
        rag_service.delete_index(collection)
        return {
            "status": "success",
            "collection": collection,
            "documents_deleted": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))