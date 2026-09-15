from uuid import uuid4

from backend.parsers.document_parser import parse_document_text
from backend.repositories.vector_repository import (
    create_demo_collection,
    create_documents_collection,
    get_collection_names,
    get_collections_count,
    search_demo_points,
    search_documents,
    seed_demo_points,
    upsert_document,
)
from backend.schemas.document import DocumentCreate, SearchRequest
from backend.services.embedding_service import create_embedding


def get_health_status() -> dict:
    return {
        "status": "healthy",
        "qdrant": "connected",
        "collections": get_collections_count(),
    }


def list_collections() -> list[str]:
    return get_collection_names()


def create_demo_documents_collection() -> None:
    create_demo_collection()


def seed_demo_documents() -> None:
    seed_demo_points()


def search_demo_documents() -> list[dict]:
    return search_demo_points()


def create_real_documents_collection() -> None:
    create_documents_collection()


def seed_real_document(document: DocumentCreate) -> dict:
    document_id = str(uuid4())
    text = parse_document_text(document.text)
    vector = create_embedding(text)

    upsert_document(
        document_id=document_id,
        vector=vector,
        text=text,
        source=document.source,
        category=document.category,
    )

    return {
        "message": "Document stored successfully",
        "id": document_id,
        "text": text,
        "source": document.source,
        "category": document.category,
    }


def search_real_documents(request: SearchRequest) -> dict:
    query_vector = create_embedding(request.query)
    results = search_documents(
        query_vector=query_vector,
        limit=request.limit,
        category=request.category,
    )

    return {
        "query": request.query,
        "category": request.category,
        "results": results,
    }
