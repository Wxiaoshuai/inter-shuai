"""Milvus client initialization module."""

from typing import Optional, List, Dict, Any
from pymilvus import MilvusClient, connections

from src.config import settings


class MilvusClientManager:
    """Milvus client manager for connection pooling."""

    def __init__(self):
        self._client: Optional[MilvusClient] = None
        self._connection_uri: Optional[str] = None
        self._connected = False

    @property
    def client(self) -> MilvusClient:
        """Get or create Milvus client."""
        if self._client is None:
            self._connection_uri = self._connection_uri or settings.milvus_uri
            self._client = MilvusClient(uri=self._connection_uri)
        return self._client

    def connect(self, uri: Optional[str] = None) -> None:
        """Connect to Milvus server."""
        self._connection_uri = uri or settings.milvus_uri

        # Parse host and port for ORM-style connection
        uri_str = self._connection_uri
        if uri_str.startswith("http://"):
            uri_str = uri_str[7:]
        elif uri_str.startswith("https://"):
            uri_str = uri_str[8:]

        if ":" in uri_str:
            host, port_str = uri_str.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 19530
        else:
            host = uri_str
            port = 19530

        # Ensure ORM-style connection for langchain compatibility
        if not connections.has_connection("default"):
            connections.connect(host=host, port=port, alias="default")

        # Create MilvusClient
        self._client = MilvusClient(uri=self._connection_uri)
        self._connected = True

    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        if self._connected:
            try:
                connections.disconnect(alias="default")
            except Exception:
                pass
            self._connected = False
        if self._client:
            self._client.close()
            self._client = None

    def list_collections(self) -> List[str]:
        """List all collections."""
        return self.client.list_collections()

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics."""
        return self.client.get_collection_stats(collection_name)

    def has_collection(self, collection_name: str) -> bool:
        """Check if collection exists."""
        return collection_name in self.list_collections()

    def create_collection(
        self,
        collection_name: str,
        dimension: int = 1024,
        metric_type: str = "COSINE",
    ) -> None:
        """Create a new collection."""
        if not self.has_collection(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                metric_type=metric_type,
                auto_id=True,
            )

    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection."""
        if self.has_collection(collection_name):
            self.client.drop_collection(collection_name)


# Global client manager
milvus_manager = MilvusClientManager()