import pymupdf

from backend.parsers.document_parser import DocumentParser
from backend.schemas.document import DocumentPage

class PdfParser(DocumentParser):
    
    def extract_pages(self, file_bytes: bytes) -> list[DocumentPage]:
        
        # Here, I am opening the PDF from memory bytes instead of providing a disk path.
        # Concept - PDF bytes -> PyMuPDF -> document object
        document = pymupdf.open(
            stream=file_bytes,
            filetype="pdf"
        )
        
        pages: list[DocumentPage] = []
        
        for index,page in enumerate(document, start=1):
            text = page.get_text("text", sort=True)
            pages.append(DocumentPage(page_number=index, text=text))
            
        document.close()
        
        return pages
    