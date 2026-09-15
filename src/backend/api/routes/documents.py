from fastapi import APIRouter

from backend.schemas.document import DocumentCreate, SearchRequest
from backend.services.document_service import (
    create_demo_documents_collection,
    create_real_documents_collection,
    get_health_status,
    list_collections,
    search_demo_documents,
    search_real_documents,
    seed_demo_documents,
    seed_real_document,
)
from backend.services.embedding_service import create_embedding

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "IntelliDocs API is running"
    }


@router.get("/embeddings/test")
def test_embedding():
    text = "Employees get 12 casual leaves per year."
    vector = create_embedding(text)

    return {
        "text": text,
        "vector_size": len(vector),
        "vector_preview": vector[:5],
    }


@router.get("/health")
def health_check():
    return get_health_status()


@router.get("/collections")
def get_collections():
    return {
        "collections": list_collections()
    }


@router.post("/collections/documents")
def create_documents_collection():
    create_demo_documents_collection()
    return {
        "message": "Documents collection created successfully"
    }


@router.post("/documents/seed")
def seed_documents():
    seed_demo_documents()
    return {
        "message": "Documents inserted successfully"
    }


@router.get("/documents/search")
def search_documents():
    return {
        "results": search_demo_documents()
    }


# ! Store Real Embeddings in Qdrant
@router.post("/collections/documents-v2")
def create_documents_v2_collection():
    create_real_documents_collection()
    return {
        "message": "Documents_v2 collection created successfully"
    }


@router.post("/documents-v2/seed")
def seed_real_documents(document: DocumentCreate):
    return seed_real_document(document)


@router.post("/documents-v2/search")
def search_documents_v2(request: SearchRequest):
    return search_real_documents(request)
