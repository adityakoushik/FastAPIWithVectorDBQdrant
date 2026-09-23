from fastapi import APIRouter, Depends, File, Form, UploadFile
from backend.api.dependencies import get_document_controller
from backend.controllers.document_controller import DocumentController


router = APIRouter(prefix="/documents", tags=["Documents"])

# file: UploadFile = File(...) meaning that file parameter is required and must be provided in the request body as a file upload. The File(...) indicates that this parameter is expected to be a file, and FastAPI will handle the file upload process for you.

# category: str | None = Form(None), means that the category parameter is optional and can be provided in the request body as form data. The Form(None) indicates that this parameter is expected to be sent as form data, and if it's not provided, it will default to None.

# controller: DocumentController = Depends(get_document_controller), means that the controller parameter is a dependency that will be automatically injected by FastAPI. The Depends(get_document_controller) indicates that FastAPI should call the get_document_controller function to obtain an instance of DocumentController, which will then be passed to the upload_document function.
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str | None = Form(None),
    controller: DocumentController = Depends(get_document_controller),
):
    return await controller.upload_pdf(file, category=category)
