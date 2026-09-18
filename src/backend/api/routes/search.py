from fastapi import APIRouter, Depends

from backend.api.dependencies import get_search_controller
from backend.controllers.search_controller import SearchController
from backend.schemas.search import SearchRequest, SearchResponse


router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    controller: SearchController = Depends(get_search_controller),
) -> SearchResponse:
    return controller.search(request)
