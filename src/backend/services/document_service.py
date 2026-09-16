from backend.parsers.document_parser import DocumentParser
from backend.schemas.document import DocumentPage


class DocumentService:
    
    def __init__(self, parser: DocumentParser):
        self.parser = parser
        
    def extract_pages(self, file_bytes: bytes) -> list[DocumentPage]:
        return self.parser.extract_pages(file_bytes)
    