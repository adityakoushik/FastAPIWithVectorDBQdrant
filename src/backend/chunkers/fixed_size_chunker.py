from backend.chunkers.text_chunker import TextChunker
from backend.schemas.document import DocumentChunk, DocumentPage


class FixedSizeChunker(TextChunker):
    """Split each page into overlapping character windows, preserving its source."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, pages: list[DocumentPage]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.overlap

        for page in pages:
            for start in range(0, len(page.text), step):
                end = start + self.chunk_size
                chunk_text = page.text[start:end].strip()
                if chunk_text:
                    chunks.append(DocumentChunk(
                        chunk_index=len(chunks),
                        page_number=page.page_number,
                        text=chunk_text,
                    ))
                # The final window already contains the remaining page text.
                if end >= len(page.text):
                    break

        return chunks
