from html import parser

from fastapi import APIRouter, Depends, File, UploadFile

from backend.api.dependencies import get_document_controller
from backend.controllers.document_controller import DocumentController
from backend.parsers.pdf_parser import PdfParser
from backend.services.document_service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# UploadFile represent the upload file
# File(...) = ... called Ellipsis
# Here, the `...` inside `File(...)` indicates to FastAPI that this `file` parameter is required; meaning, the client must upload a file.

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    controller: DocumentController = Depends(
        get_document_controller
    )
):
    return await controller.upload_pdf(file)
    