"""Provide routes with controllers created at startup.

Depends(get_search_controller) → request.app → state.container → controller.
Depends does not create an app-wide singleton. Requests share resources
because objects come from the same container.
"""

from fastapi import HTTPException, Request

from backend.controllers.document_controller import DocumentController
from backend.controllers.search_controller import SearchController
from backend.core.container import AppContainer


def get_container(request: Request) -> AppContainer:
    # app.state stores application-level data.
    # Only the API layer needs to know about FastAPI.
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Application is not ready")
    return container


def get_document_controller(request: Request) -> DocumentController:
    return get_container(request).document_controller


def get_search_controller(request: Request) -> SearchController:
    return get_container(request).search_controller
