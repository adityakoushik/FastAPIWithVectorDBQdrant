from abc import ABC, abstractmethod
from src.backend.parsers.document_parser import DocumentParser


# ABC means Actual Base Class
# We are defining the rule or contract here. It means which class is taking DocumentParser then they must implement extract_text()
# file_bytes means, This is because, with an API upload, we receive the file content in memory as bytes.
class DocumentParser(ABC):
    
    @abstractmethod
    def extract_text(self, file_bytes) -> str:
        pass