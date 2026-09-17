from fastapi import APIRouter, Depends, File, Form, UploadFile
from backend.api.dependencies import get_document_controller
from backend.controllers.document_controller import DocumentController


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str | None = Form(None),
    controller: DocumentController = Depends(get_document_controller),
):
    return await controller.upload_pdf(file, category=category)
