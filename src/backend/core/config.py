import os

from pydantic import BaseModel


class Settings(BaseModel):
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333/")
    demo_documents_collection: str = os.getenv("DEMO_DOCUMENTS_COLLECTION", "documents")
    documents_collection: str = os.getenv("DOCUMENTS_COLLECTION", "documents_v2")
    demo_vector_size: int = int(os.getenv("DEMO_VECTOR_SIZE", "3"))
    embedding_vector_size: int = int(os.getenv("EMBEDDING_VECTOR_SIZE", "384"))
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    search_score_threshold: float = float(os.getenv("SEARCH_SCORE_THRESHOLD", "0.4"))


settings = Settings()
