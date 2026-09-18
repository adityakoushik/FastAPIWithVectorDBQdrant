import unittest
from contextlib import closing
from unittest.mock import Mock
from uuid import UUID

from qdrant_client import QdrantClient
from backend.repositories.vector_repository import VectorRepository
from backend.repositories.qdrant_vector_repository import QdrantVectorRepository
from backend.schemas.document import DocumentChunk, DocumentPage
from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService


class FakeRepository(VectorRepository):
    def __init__(self):
        self.calls = []

    def store_chunks(self, **kwargs):
        self.calls.append(kwargs)

    def search(self, query_vector, limit, score_threshold, category=None):
        return []


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.pages = [DocumentPage(page_number=1, text='One'), DocumentPage(page_number=2, text='Two')]
        self.chunks = [DocumentChunk(chunk_index=i, page_number=i+1, text=p.text) for i, p in enumerate(self.pages)]
        self.parser = Mock()
        self.parser.extract_pages.return_value = self.pages
        self.chunker = Mock()
        self.chunker.chunk.return_value = self.chunks
        self.embedding = Mock()
        self.embedding.embed_batch.return_value = [[1., 0.], [0., 1.]]
        self.repository = FakeRepository()
        self.service = DocumentService(self.parser, self.chunker, self.embedding, self.repository)

    def test_batch_and_metadata_remain_aligned(self):
        result = self.service.ingest_document(b'pdf', 'handbook.pdf', 'HR')
        UUID(result['document_id'])
        self.parser.extract_pages.assert_called_once_with(b'pdf')
        self.chunker.chunk.assert_called_once_with(self.pages)
        self.embedding.embed_batch.assert_called_once_with(['One', 'Two'])
        self.assertEqual(result['total_pages'], 2)
        self.assertEqual(result['total_chunks'], 2)
        self.assertEqual(self.repository.calls, [dict(chunks=self.chunks, vectors=[[1., 0.], [0., 1.]], document_id=result['document_id'], source='handbook.pdf', category='HR')])

    def test_empty_document_does_not_embed_or_store(self):
        self.chunker.chunk.return_value = []
        self.assertEqual(self.service.ingest_document(b'pdf')['total_chunks'], 0)
        self.embedding.embed_batch.assert_not_called()
        self.assertEqual(self.repository.calls, [])

    def test_embedding_failure_does_not_store(self):
        self.embedding.embed_batch.side_effect = RuntimeError('model failure')
        with self.assertRaises(RuntimeError):
            self.service.ingest_document(b'pdf')
        self.assertEqual(self.repository.calls, [])

    def test_repository_failure_is_not_reported_as_success(self):
        self.service.vector_repository = Mock()
        self.service.vector_repository.store_chunks.side_effect = RuntimeError('database failure')
        with self.assertRaises(RuntimeError):
            self.service.ingest_document(b'pdf')

    def test_qdrant_round_trip_and_distinct_point_ids(self):
        with closing(QdrantClient(':memory:')) as client:
            repository = QdrantVectorRepository(client, 'test_documents')
            for _ in range(2):
                repository.store_chunks(self.chunks, [[1., 0.], [0., 1.]], 'doc', 'handbook.pdf', 'HR')
            points, _ = client.scroll('test_documents', with_vectors=True)
            self.assertEqual(len(points), 4)
            self.assertEqual(len({p.id for p in points}), 4)
            for point in points:
                UUID(point.id)
                index = point.payload['chunk_index']
                self.assertEqual(point.payload, dict(document_id='doc', text=self.chunks[index].text, page_number=index+1, chunk_index=index, source='handbook.pdf', category='HR'))
                self.assertEqual(point.vector, [[1., 0.], [0., 1.]][index])

    def test_invalid_vectors_fail_before_database_calls(self):
        client = Mock()
        repository = QdrantVectorRepository(client, 'test')
        for vectors in ([[1., 0.]], [[], []], [[1.], [1., 2.]]):
            with self.subTest(vectors=vectors), self.assertRaises(ValueError):
                repository.store_chunks(self.chunks, vectors, 'doc')
        repository.store_chunks([], [], 'doc')
        self.assertEqual(client.mock_calls, [])

    def test_embedding_single_batch_and_empty(self):
        service = EmbeddingService.__new__(EmbeddingService)
        service.model = Mock()
        service.model.encode.return_value.tolist.return_value = [[1., 2.], [3., 4.]]
        self.assertEqual(service.embed_batch(['one', 'two']), [[1., 2.], [3., 4.]])
        service.model.encode.assert_called_once_with(['one', 'two'])
        service.model.reset_mock()
        self.assertEqual(service.embed_batch([]), [])
        service.model.encode.assert_not_called()
        service.model.encode.return_value.tolist.return_value = [1., 2.]
        self.assertEqual(service.embed_text('query'), [1., 2.])
        service.model.encode.assert_called_once_with('query')

