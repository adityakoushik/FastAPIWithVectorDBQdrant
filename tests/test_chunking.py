import unittest
from unittest.mock import Mock, patch
from uuid import UUID
from backend.api.dependencies import get_document_controller
from backend.controllers.document_controller import DocumentController
from backend.parsers.pdf_parser import PdfParser
from backend.services.document_service import DocumentService
from test_ingestion import FakeRepository

import pymupdf
from fastapi.testclient import TestClient

from backend.chunkers.fixed_size_chunker import FixedSizeChunker
from backend.main import app
from backend.schemas.document import DocumentPage


class FixedSizeChunkerTests(unittest.TestCase):
    def test_overlap_and_source_pages(self):
        chunks = FixedSizeChunker(5, 2).chunk([
            DocumentPage(page_number=2, text="abcdefghij"),
            DocumentPage(page_number=4, text="xyz"),
        ])
        self.assertEqual([c.text for c in chunks], ["abcde", "defgh", "ghij", "xyz"])
        self.assertEqual([c.chunk_index for c in chunks], [0, 1, 2, 3])
        self.assertEqual([c.page_number for c in chunks], [2, 2, 2, 4])

    def test_no_redundant_tail(self):
        for size in (4, 5, 8):
            with self.subTest(size=size):
                chunks = FixedSizeChunker(5, 2).chunk([
                    DocumentPage(page_number=1, text="abcdefgh"[:size]),
                ])
                self.assertEqual(len(chunks), 1 if size <= 5 else 2)

    def test_empty_pages_and_whitespace(self):
        chunker = FixedSizeChunker(5, 0)
        self.assertEqual(chunker.chunk([]), [])
        chunks = chunker.chunk([
            DocumentPage(page_number=1, text=""),
            DocumentPage(page_number=2, text="      "),
            DocumentPage(page_number=3, text=" abc "),
        ])
        self.assertEqual([c.model_dump() for c in chunks], [
            {"chunk_index": 0, "page_number": 3, "page_end": None, "text": "abc"},
        ])

    def test_invalid_configuration(self):
        for size, overlap in [(0, 0), (-1, 0), (5, -1), (5, 5), (5, 6)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    FixedSizeChunker(size, overlap)

    def test_pdf_upload(self):
        with pymupdf.open() as pdf:
            for text in ["Employees receive 12 casual leaves per year.", "Health insurance covers children."]:
                pdf.new_page().insert_text((72, 72), text)
            file_bytes = pdf.tobytes()
        repository = FakeRepository()
        embedding = Mock()
        embedding.embed_batch.return_value = [[1., 0.], [0., 1.]]
        controller = DocumentController(DocumentService(
            PdfParser(), FixedSizeChunker(500, 0), embedding, repository,
        ))
        app.dependency_overrides[get_document_controller] = lambda: controller
        self.addCleanup(app.dependency_overrides.clear)
        # Lifespan চলবে; এই route test-এ real model/database দরকার নেই।
        with patch('backend.main.build_container', return_value=Mock()), TestClient(app) as client:
            response = client.post("/documents/upload", files={
                "file": ("handbook.pdf", file_bytes, "application/pdf"),
            }, data={"category": "HR"})
            self.assertEqual(client.get("/docs").status_code, 200)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["filename"], "handbook.pdf")
        self.assertEqual(result["total_pages"], 2)
        UUID(result["document_id"])
        self.assertEqual(result["total_chunks"], 2)
        stored = repository.calls[0]
        self.assertEqual(stored['source'], 'handbook.pdf')
        self.assertEqual(stored['category'], 'HR')
        self.assertEqual([c.page_number for c in stored['chunks']], [1, 2])
        self.assertEqual([c.chunk_index for c in stored['chunks']], [0, 1])
        self.assertIn('12 casual leaves', stored['chunks'][0].text)


if __name__ == '__main__':
    unittest.main()
