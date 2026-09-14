from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embedding(text: str) -> list[float]:
    embedding = embedding_model.encode(text)
    return embedding.tolist()
