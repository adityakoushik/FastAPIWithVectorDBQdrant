from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

from backend.core.config import settings


embedding_model = SentenceTransformer(settings.embedding_model_name)


def create_embedding(text: str) -> list[float]:
    embedding = embedding_model.encode(text)
    return embedding.tolist()
