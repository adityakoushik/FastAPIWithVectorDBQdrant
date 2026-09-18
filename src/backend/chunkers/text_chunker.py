from abc import ABC, abstractmethod

from backend.schemas.document import DocumentChunk, DocumentPage


class TextChunker(ABC):
    @abstractmethod
    def chunk(self, pages: list[DocumentPage]) -> list[DocumentChunk]:
        pass
