import unittest
from contextlib import closing
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from backend.repositories.vector_repository import VectorRepository
from backend.repositories.qdrant_vector_repository import QdrantVectorRepository
from backend.schemas.document import DocumentChunk
from backend.schemas.search import SearchResult
from backend.services.search_service import SearchService
from backend.controllers.search_controller import SearchController


class FakeVectorRepository(VectorRepository):
    def __init__(self):
        self.search_results = []
        self.search_calls = []

    def store_chunks(self, **kwargs):
        raise NotImplementedError

    def search(self, query_vector, limit, score_threshold, category=None, document_id=None):
        self.search_calls.append((query_vector, limit, score_threshold, category, document_id))
        return self.search_results


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.embedding = Mock()
        self.embedding.embed_text.return_value = [1., 0.]
        self.repository = FakeVectorRepository()
        self.service = SearchService(self.embedding, self.repository)

    def test_service_embeds_query_and_forwards_search_options(self):
        expected = SearchResult(id='point', score=0.9, text='12 days')
        self.repository.search_results = [expected]
        self.assertEqual(self.service.search('leave?', 5, 0.7, 'HR', 'doc'), [expected])
        self.embedding.embed_text.assert_called_once_with('leave?')
        self.assertEqual(self.repository.search_calls, [([1., 0.], 5, 0.7, 'HR', 'doc')])

    def test_embedding_failure_does_not_search(self):
        self.embedding.embed_text.side_effect = RuntimeError('embedding failed')
        with self.assertRaises(RuntimeError):
            self.service.search('leave?', 3, 0.4)
        self.assertEqual(self.repository.search_calls, [])

    def test_qdrant_search_filters_limits_threshold_and_metadata(self):
        with closing(QdrantClient(':memory:')) as client:
            repository = QdrantVectorRepository(client, 'search_test')
            chunk = DocumentChunk(text='12 days', page_number=4, page_end=5, chunk_index=7)
            repository.store_chunks([chunk], [[1., 0.]], 'doc', 'handbook.pdf', 'HR')
            repository.store_chunks([chunk], [[1., 0.]], 'other', 'tech.pdf', 'IT')
            repository.store_chunks([chunk], [[0., 1.]], 'unrelated', category='HR')
            results = repository.search([1., 0.], 10, 0.4, 'HR')
            self.assertEqual(len(results), 1)
            self.assertIsInstance(results[0], SearchResult)
            self.assertEqual(results[0].model_dump(exclude={'id', 'score'}), dict(
                text='12 days', document_id='doc', source='handbook.pdf',
                category='HR', page_number=4, page_end=5, chunk_index=7,
            ))
            self.assertAlmostEqual(results[0].score, 1.)
            self.assertEqual(len(repository.search([1., 0.], 10, 0.4)), 2)
            self.assertEqual(len(repository.search([1., 0.], 1, 0.4)), 1)
            self.assertEqual(repository.search([1., 0.], 10, 1.1), [])
            self.assertEqual(repository.search([1., 0.], 10, 0.4, 'missing'), [])
            self.assertEqual([r.document_id for r in repository.search([1., 0.], 10, 0.4, document_id='doc')], ['doc'])
            self.assertEqual(repository.search([1., 0.], 10, 0.4, 'IT', 'doc'), [])
            self.assertEqual(repository.search([1., 0.], 10, 0.4, document_id='missing'), [])
            client.upsert('search_test', [PointStruct(id=42, vector=[1., 0.])])
            missing_payload = next(r for r in repository.search([1., 0.], 10, 0.4) if r.id == '42')
            self.assertEqual(missing_payload.text, '')
            self.assertIsNone(missing_payload.document_id)
            self.assertIsNone(missing_payload.page_number)

    def test_api_defaults_metadata_empty_results_and_custom_options(self):
        # Prevent the application's client constructor from checking a remote server.
        with patch('qdrant_client.QdrantClient'):
            from backend.main import app
            from backend.api.dependencies import get_search_controller
        app.dependency_overrides[get_search_controller] = lambda: SearchController(self.service)
        self.addCleanup(app.dependency_overrides.pop, get_search_controller)
        # Dependency override startup থামায় না, তাই builder-ও fake করি।
        with patch('backend.main.build_container', return_value=Mock()), TestClient(app) as client:
            response = client.post('/search', json={'query': 'leave?'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'query': 'leave?', 'total_results': 0, 'results': []})
            self.assertEqual(self.repository.search_calls[-1], ([1., 0.], 3, 0.4, None, None))
            result = SearchResult(id='point', score=0.9, text='12 days', source='handbook.pdf', page_number=4)
            self.repository.search_results = [result]
            response = client.post('/search', json={
                'query': 'leave?', 'limit': 5, 'score_threshold': 0.7, 'category': 'HR', 'document_id': 'doc',
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'query': 'leave?', 'total_results': 1, 'results': [result.model_dump()]})
            self.assertEqual(self.repository.search_calls[-1], ([1., 0.], 5, 0.7, 'HR', 'doc'))
            self.assertEqual(client.post('/search', json={}).status_code, 422)
