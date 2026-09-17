from uuid import uuid4
from backend.chunkers.text_chunker import TextChunker
from backend.parsers.document_parser import DocumentParser
from backend.repositories.vector_repository import VectorRepository
from backend.schemas.document import DocumentChunk
from backend.services.embedding_service import EmbeddingService


class DocumentService:
    def __init__(
        self, parser: DocumentParser, chunker: TextChunker,
        embedding_service: EmbeddingService, vector_repository: VectorRepository,
    ):
        self.parser = parser
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

    def process_document(self, file_bytes: bytes) -> list[DocumentChunk]:
        return self.chunker.chunk(self.parser.extract_pages(file_bytes))

    def ingest_document(
        self, file_bytes: bytes, source: str | None = None, category: str | None = None,
    ) -> dict:
        document_id = str(uuid4())
        pages = self.parser.extract_pages(file_bytes)
        chunks = self.chunker.chunk(pages)
        if chunks:
            vectors = self.embedding_service.embed_batch([chunk.text for chunk in chunks])
            self.vector_repository.store_chunks(
                chunks=chunks, vectors=vectors, document_id=document_id,
                source=source, category=category,
            )
        return {
            "document_id": document_id, "total_pages": len(pages),
            "total_chunks": len(chunks),
        }
