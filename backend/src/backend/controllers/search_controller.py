from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search_service import SearchService


class SearchController:
    def __init__(self, search_service: SearchService):
        self.search_service = search_service

    def search(self, request: SearchRequest) -> SearchResponse:
        results = self.search_service.search(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            category=request.category,
            document_id=request.document_id,
        )
        return SearchResponse(
            query=request.query, total_results=len(results), results=results,
        )
