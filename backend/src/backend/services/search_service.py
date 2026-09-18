from backend.repositories.vector_repository import VectorRepository
from backend.schemas.search import SearchResult
from backend.services.embedding_service import EmbeddingService


class SearchService:
    def __init__(
        self, embedding_service: EmbeddingService, vector_repository: VectorRepository,
        default_limit: int = 3, default_score_threshold: float = 0.4,
    ):
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        # Bootstrap Settings থেকে সাধারণ সংখ্যা দেয়। Service-এর .env বা
        # request.app.state জানার দরকার নেই; আলাদাভাবে test করা যায়।
        self.default_limit = default_limit
        self.default_score_threshold = default_score_threshold

    def search(
        self, query: str, limit: int | None = None, score_threshold: float | None = None,
        category: str | None = None,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        # None-ই শুধু অনুপস্থিত value। threshold=0 বৈধ, তাই `or` ব্যবহার নয়।
        limit = self.default_limit if limit is None else limit
        score_threshold = self.default_score_threshold if score_threshold is None else score_threshold
        query_vector = self.embedding_service.embed_text(query)
        return self.vector_repository.search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            category=category,
            document_id=document_id,
        )
