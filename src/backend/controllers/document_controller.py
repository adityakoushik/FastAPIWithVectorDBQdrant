from fastapi import UploadFile, File
from backend.services.document_service import DocumentService

# UploadFile represent the upload file
class DocumentController:
    
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service
        
    async def upload_pdf(self, file: UploadFile):
        file_byte = await file.read()
        pages = self.document_service.extract_pages(file_byte)
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "total_pages": len(pages),
            "pages": pages
        }