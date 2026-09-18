from functools import lru_cache
from backend.core.config import get_settings


class EmbeddingService:
    def __init__(self, model_name: str | None = None):
        # Bootstrap model-এর নাম দেয় এবং এই object startup-এ একবার বানায়।
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name or get_settings().embedding_model)

    def embed_text(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self.model.encode(texts).tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """পুরোনো lesson-এর helper; নতুন API lifespan-এর model ব্যবহার করে।"""
    return EmbeddingService()


def create_embedding(text: str) -> list[float]:
    """Compatibility entry point for the earlier search lessons."""
    return get_embedding_service().embed_text(text)
