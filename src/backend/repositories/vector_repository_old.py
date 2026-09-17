from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from backend.core.config import settings
from backend.db.qdrant import qdrant_client


def get_collections_count() -> int:
    collections = qdrant_client.get_collections()
    return len(collections.collections)


def get_collection_names() -> list[str]:
    collections = qdrant_client.get_collections()
    return [
        collection.name for collection in collections.collections
    ]


def create_demo_collection() -> None:
    qdrant_client.create_collection(
        collection_name=settings.demo_documents_collection,
        # VectorParams decides how vectors are stored in Qdrant.
        vectors_config=VectorParams(
            size=settings.demo_vector_size,
            distance=Distance.COSINE,
        ),
    )


def seed_demo_points() -> None:
    # These vectors are 3 dimensional manual vectors for learning purpose.
    points = [
        PointStruct(
            id=1,
            vector=[1.0, 0.0, 0.0],
            payload={
                "text": "Employees get 12 casual leaves per year."
            },
        ),
        PointStruct(
            id=2,
            vector=[0.0, 1.0, 0.0],
            payload={
                "text": "Docker packages applications into containers."
            },
        ),
        PointStruct(
            id=3,
            vector=[0.0, 0.0, 1.0],
            payload={
                "text": "React is used for building user interfaces."
            },
        ),
    ]
    qdrant_client.upsert(
        collection_name=settings.demo_documents_collection,
        points=points,
    )


def search_demo_points() -> list[dict]:
    # Stored: [1.0, 0.0, 0.0], query: [0.9, 0.1, 0.0]
    results = qdrant_client.query_points(
        collection_name=settings.demo_documents_collection,
        query=[0.9, 0.1, 0.0],
        limit=3,
    )
    return _format_points(results.points)


def create_documents_collection() -> None:
    qdrant_client.create_collection(
        collection_name=settings.documents_collection,
        vectors_config=VectorParams(
            size=settings.embedding_vector_size,
            distance=Distance.COSINE,
        ),
    )


def upsert_document(
    document_id: str,
    vector: list[float],
    text: str,
    source: str | None,
    category: str | None,
) -> None:
    point = PointStruct(
        id=document_id,
        vector=vector,
        payload={
            "text": text,
            "source": source,
            "category": category,
        },
    )
    qdrant_client.upsert(
        collection_name=settings.documents_collection,
        points=[point],
    )


def search_documents(
    query_vector: list[float],
    limit: int,
    category: str | None,
) -> list[dict]:
    query_filter = _build_category_filter(category)
    results = qdrant_client.query_points(
        collection_name=settings.documents_collection,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=settings.search_score_threshold,
    )
    return _format_points(results.points)


def _build_category_filter(category: str | None) -> Filter | None:
    if not category:
        return None

    return Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value=category),
            )
        ]
    )


def _format_points(points) -> list[dict]:
    return [
        {
            "id": point.id,
            "score": point.score,
            "payload": point.payload,
        }
        for point in points
    ]
