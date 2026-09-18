from abc import ABC, abstractmethod
from backend.schemas.document import DocumentChunk
from backend.schemas.search import SearchResult


class VectorRepository(ABC):
    @abstractmethod
    def store_chunks(
        self, chunks: list[DocumentChunk], vectors: list[list[float]],
        document_id: str, source: str | None = None, category: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    def search(
        self, query_vector: list[float], limit: int,
        score_threshold: float, category: str | None = None,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        pass
