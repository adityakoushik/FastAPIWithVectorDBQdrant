from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, MatchValue, PointStruct, ScoredPoint, VectorParams,
)
from backend.repositories.vector_repository import VectorRepository
from backend.schemas.document import DocumentChunk
from backend.schemas.search import SearchResult


class QdrantVectorRepository(VectorRepository):
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    def search(
        self, query_vector: list[float], limit: int,
        score_threshold: float, category: str | None = None,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        conditions = []
        if category:
            conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )
        if document_id is not None:
            conditions.append(
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            )
        query_filter = Filter(must=conditions) if conditions else None
        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return [self._map_search_result(point) for point in result.points]

    def _map_search_result(self, point: ScoredPoint) -> SearchResult:
        payload = point.payload or {}
        return SearchResult(
            id=str(point.id),
            score=point.score,
            text=payload.get("text", ""),
            document_id=payload.get("document_id"),
            source=payload.get("source"),
            category=payload.get("category"),
            page_number=payload.get("page_number"),
            page_end=payload.get("page_end"),
            chunk_index=payload.get("chunk_index"),
        )

    def store_chunks(
        self, chunks: list[DocumentChunk], vectors: list[list[float]],
        document_id: str, source: str | None = None, category: str | None = None,
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors count must match")
        if not chunks:
            return
        size = len(vectors[0])
        if not size or any(len(vector) != size for vector in vectors):
            raise ValueError("Vectors must have the same nonzero dimension")
        points = [
            PointStruct(
                id=str(uuid4()), vector=vector,
                payload={
                    "document_id": document_id, "text": chunk.text,
                    "page_number": chunk.page_number, "chunk_index": chunk.chunk_index,
                    **({"page_end": chunk.page_end} if chunk.page_end is not None else {}),
                    "source": source, "category": category,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        # If no collection exists, create it with the appropriate vector size and distance metric
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
        # Stores chunk vectors and payload within the collection.
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
