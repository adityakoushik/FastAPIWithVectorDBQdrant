from backend.controllers.document_controller import (
    DocumentController
)
from backend.parsers.pdf_parser import PdfParser
from backend.services.document_service import DocumentService


def get_document_controller() -> DocumentController:

    parser = PdfParser()

    service = DocumentService(
        parser=parser
    )

    return DocumentController(
        document_service=service
    )