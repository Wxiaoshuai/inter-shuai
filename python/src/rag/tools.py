"""RAG tools for document loading, splitting, and vector storage."""

from typing import List, Optional, Tuple
from pathlib import Path
import json

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient

from src.core.embedding import get_dashscope_embedding
from src.config import settings


class MilvusVectorStore:
    """Direct Milvus vector store using MilvusClient."""

    def __init__(
        self,
        uri: str,
        collection_name: str,
        embedding,
        dimension: int = 1024,
    ):
        self.uri = uri
        self.collection_name = collection_name
        self.embedding = embedding
        self.dimension = dimension
        self._client = MilvusClient(uri=uri)

    def create_collection(self) -> None:
        """Create collection if not exists."""
        if not self._client.has_collection(self.collection_name):
            self._client.create_collection(
                collection_name=self.collection_name,
                dimension=self.dimension,
                metric_type="COSINE",
                auto_id=True,
            )

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the collection."""
        self.create_collection()

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata or {} for doc in documents]

        # Generate embeddings
        embeddings = self.embedding.embed_documents(texts)

        # Prepare data for insertion
        data = [
            {"text": text, "vector": emb, "metadata": json.dumps(meta, ensure_ascii=False)}
            for text, emb, meta in zip(texts, embeddings, metadatas)
        ]

        self._client.insert(
            collection_name=self.collection_name,
            data=data,
        )

    def similarity_search_with_score(
        self, query: str, k: int = 3, filter_str: Optional[str] = None
    ) -> List[tuple]:
        """Search similar documents with scores."""
        self.create_collection()

        query_vector = self.embedding.embed_query(query)

        results = self._client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=k,
            filter=filter_str,
            output_fields=["text", "metadata"],
        )

        docs = []
        for hit in results[0]:
            text = hit.get("entity", {}).get("text", "")
            metadata_str = hit.get("entity", {}).get("metadata", "{}")
            try:
                metadata = json.loads(metadata_str)
            except:
                metadata = {}
            doc = Document(page_content=text, metadata=metadata)
            docs.append((doc, hit.get("distance", 0.0)))

        return docs


class RAGTools:
    """RAG tools for document processing and vector storage."""

    def __init__(
        self,
        collection_name: str = "default",
        embedding_model: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize RAG tools.

        Args:
            collection_name: Milvus collection name
            embedding_model: Embedding model name
            chunk_size: Default chunk size for splitting
            chunk_overlap: Default chunk overlap
        """
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.embedding = get_dashscope_embedding(
            model=embedding_model or settings.bailian_embedding_model
        )

        self._vector_store: Optional[MilvusVectorStore] = None

    @property
    def vector_store(self) -> MilvusVectorStore:
        """Get or create vector store."""
        if self._vector_store is None:
            self._vector_store = MilvusVectorStore(
                uri=settings.milvus_uri,
                collection_name=self.collection_name,
                embedding=self.embedding,
            )
        return self._vector_store

    def load_documents_from_folder(self, folder_path: str) -> List[Document]:
        """
        Load documents from a folder.

        Args:
            folder_path: Path to folder containing documents

        Returns:
            List of loaded documents
        """
        documents = []
        folder = Path(folder_path)

        loaders = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': TextLoader,
            '.docx': Docx2txtLoader,
        }

        for ext, loader_class in loaders.items():
            for file_path in folder.rglob(f"*{ext}"):
                try:
                    if loader_class == TextLoader:
                        for encoding in ['utf-8', 'gbk', 'gb2312']:
                            try:
                                loader = loader_class(str(file_path), encoding=encoding)
                                docs = loader.load()
                                documents.extend(docs)
                                break
                            except UnicodeDecodeError:
                                continue
                    else:
                        loader = loader_class(str(file_path))
                        docs = loader.load()
                        documents.extend(docs)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

        return documents

    def load_documents(
        self,
        documents: List[dict],
        content_key: str = "content",
        metadata_key: str = "metadata",
    ) -> List[Document]:
        """
        Convert raw documents to Document objects.

        Args:
            documents: List of document dicts or Pydantic Document models
            content_key: Key for content field (for dicts)
            metadata_key: Key for metadata field (for dicts)

        Returns:
            List of Document objects
        """
        docs = []
        for doc in documents:
            # Handle Pydantic Document model
            if hasattr(doc, 'content'):
                content = doc.content
                metadata = doc.metadata or {}
            # Handle dict
            elif isinstance(doc, dict):
                content = doc.get(content_key, "")
                metadata = doc.get(metadata_key, {})
            else:
                continue

            if content:
                docs.append(Document(page_content=content, metadata=metadata or {}))
        return docs

    def split_documents(
        self,
        documents: List[Document],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Document]:
        """
        Split documents into chunks.

        Args:
            documents: List of documents
            chunk_size: Chunk size (uses default if None)
            chunk_overlap: Chunk overlap (uses default if None)

        Returns:
            List of chunked documents
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or self.chunk_size,
            chunk_overlap=chunk_overlap or self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_documents(documents)

        valid_chunks = []
        for doc in chunks:
            if hasattr(doc, 'page_content') and isinstance(doc.page_content, str):
                if doc.page_content.strip():
                    valid_chunks.append(doc)

        return valid_chunks

    def create_vector_store(self, chunks: List[Document]) -> None:
        """
        Create vector store from document chunks.

        If collection already exists, adds documents to it.
        If collection doesn't exist, creates it first.

        Args:
            chunks: List of document chunks
        """
        if not chunks:
            raise ValueError("No chunks to add to vector store")

        self._vector_store = MilvusVectorStore(
            uri=settings.milvus_uri,
            collection_name=self.collection_name,
            embedding=self.embedding,
        )

        # Only create collection if it doesn't exist
        if not self._vector_store._client.has_collection(self.collection_name):
            self._vector_store._client.create_collection(
                collection_name=self.collection_name,
                dimension=self._vector_store.dimension,
                metric_type="COSINE",
                auto_id=True,
            )

        self._vector_store.add_documents(chunks)

    def add_to_vector_store(self, chunks: List[Document]) -> None:
        """
        Add chunks to existing vector store.

        Args:
            chunks: List of document chunks
        """
        if not self._vector_store:
            self._vector_store = MilvusVectorStore(
                uri=settings.milvus_uri,
                collection_name=self.collection_name,
                embedding=self.embedding,
            )

        self._vector_store.add_documents(chunks)

    def similarity_search(
        self,
        query: str,
        k: int = 3,
        filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Perform similarity search.

        Args:
            query: Search query
            k: Number of results
            filter: Optional filter expression

        Returns:
            List of search results with id, text, score, metadata
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter_str=filter,
            )

            formatted_results = []
            for doc, score in results:
                result = {
                    "id": doc.metadata.get("id", str(hash(doc.page_content))),
                    "content": doc.page_content,
                    "score": score,
                    "metadata": doc.metadata,
                }
                formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_collection_info(self) -> dict:
        """Get collection information."""
        try:
            if not self._vector_store:
                self._vector_store = MilvusVectorStore(
                    uri=settings.milvus_uri,
                    collection_name=self.collection_name,
                    embedding=self.embedding,
                )
            if self._client.has_collection(self.collection_name):
                stats = self._client.get_collection_stats(self.collection_name)
                return {
                    "name": self.collection_name,
                    "row_count": stats.get("row_count", 0),
                    "dimension": stats.get("dimension", None),
                }
            return {"name": self.collection_name, "row_count": 0}
        except Exception as e:
            return {"name": self.collection_name, "error": str(e)}