"""Request এলে startup-এ তৈরি controller খুঁজে route-কে দাও।

Depends(get_search_controller) → request.app → state.container → controller।
Depends নিজে application-wide singleton বানায় না; একই container থেকে
object ফেরত দেওয়ার কারণেই বহু request একই resource ব্যবহার করে।
"""

from fastapi import HTTPException, Request

from backend.controllers.document_controller import DocumentController
from backend.controllers.search_controller import SearchController
from backend.core.container import AppContainer


def get_container(request: Request) -> AppContainer:
    # app.state: application-এর সঙ্গে আমাদের data রাখার জায়গা।
    # শুধু API layer এটি জানে; service-এর FastAPI জানার দরকার নেই।
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Application is not ready")
    return container


def get_document_controller(request: Request) -> DocumentController:
    return get_container(request).document_controller


def get_search_controller(request: Request) -> SearchController:
    return get_container(request).search_controller
