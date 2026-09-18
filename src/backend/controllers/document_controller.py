from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool
from backend.services.document_service import DocumentService


class DocumentController:
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service

    async def upload_pdf(self, file: UploadFile, category: str | None = None):
        file_bytes = await file.read()
        result = await run_in_threadpool(
            self.document_service.ingest_document,
            file_bytes=file_bytes, source=file.filename, category=category,
        )
        return {"filename": file.filename, **result}
