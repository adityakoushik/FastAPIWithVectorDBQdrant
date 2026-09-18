from qdrant_client import QdrantClient

from backend.core.config import settings

# Here qdrant client is python client which is used to connect with Qdrant Database.
qdrant_client = QdrantClient(
    url=settings.qdrant_url
)
