"""Class 5: আসল model download ছাড়াই configuration ও lifecycle যাচাই।"""

import asyncio
import os
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.core.bootstrap import build_container
from backend.core.config import Settings, get_settings
from backend.main import app, lifespan


class ConfigurationTests(unittest.TestCase):
    def test_environment_overrides_defaults_and_cache_reuses_object(self):
        get_settings.cache_clear()
        self.addCleanup(get_settings.cache_clear)
        with patch.dict(os.environ, {'INTC_CHUNK_SIZE': '700'}, clear=True):
            self.assertEqual(Settings(_env_file=None).chunk_size, 700)
            self.assertIs(get_settings(), get_settings())
            self.assertEqual(get_settings().chunk_size, 700)

    def test_invalid_values_and_invalid_combination_fail_fast(self):
        with patch.dict(os.environ, {}, clear=True):
            for values in (
                {'chunk_size': 0}, {'overlap_sentences': -1},
                {'oversized_overlap': -1}, {'search_default_limit': 21},
                {'search_score_threshold': 1.1},
                {'chunk_size': 500, 'oversized_overlap': 500},
            ):
                with self.subTest(values=values), self.assertRaises(ValidationError):
                    Settings(_env_file=None, **values)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, search_default_limit=7, search_score_threshold=0.6)
        self.client = Mock()
        self.embedding = Mock()
        self.embedding.embed_text.return_value = [1., 0.]

    def build(self):
        with (
            patch('backend.core.bootstrap.QdrantClient', return_value=self.client),
            patch('backend.core.bootstrap.EmbeddingService', return_value=self.embedding) as model,
            patch('backend.core.bootstrap.SpacySentenceSplitter') as splitter,
        ):
            container = build_container(self.settings)
        model.assert_called_once_with(model_name=self.settings.embedding_model)
        splitter.assert_called_once_with()
        self.client.close.assert_not_called()
        return container

    def test_services_share_model_and_repository(self):
        container = self.build()
        document = container.document_controller.document_service
        search = container.search_controller.search_service
        self.assertIs(document.embedding_service, search.embedding_service)
        self.assertIs(document.vector_repository, search.vector_repository)

    def test_requests_reuse_container_and_shutdown_closes_client(self):
        container = self.build()
        self.client.query_points.return_value.points = []
        # with-এ ঢুকলে startup; বেরোলে shutdown। দুটো request, একটি build।
        with patch('backend.main.build_container', return_value=container) as builder:
            with TestClient(app) as http:
                self.assertIs(app.state.container, container)
                self.assertEqual(http.post('/search', json={'query': 'hello'}).status_code, 200)
                self.assertEqual(self.client.query_points.call_args.kwargs['limit'], 7)
                self.assertEqual(self.client.query_points.call_args.kwargs['score_threshold'], 0.6)
                self.assertEqual(http.post('/search', json={'query': 'hello', 'score_threshold': 0}).status_code, 200)
                self.assertEqual(self.client.query_points.call_args.kwargs['score_threshold'], 0)
                builder.assert_called_once()
                self.client.close.assert_not_called()
        self.client.close.assert_called_once()
        self.assertIsNone(app.state.container)

    def test_failed_startup_closes_created_client(self):
        with (
            patch('backend.core.bootstrap.QdrantClient', return_value=self.client),
            patch('backend.core.bootstrap.SpacySentenceSplitter', side_effect=RuntimeError('load failed')),
            self.assertRaisesRegex(RuntimeError, 'load failed'),
        ):
            build_container(self.settings)
        self.client.close.assert_called_once()

    def test_lifespan_exception_still_cleans_up(self):
        container = self.build()

        async def run():
            async with lifespan(app):
                raise RuntimeError('lifetime failed')

        with patch('backend.main.build_container', return_value=container):
            with self.assertRaisesRegex(RuntimeError, 'lifetime failed'):
                asyncio.run(run())
        self.client.close.assert_called_once()
        self.assertIsNone(app.state.container)

    def test_close_failure_still_clears_app_state(self):
        container = self.build()
        self.client.close.side_effect = RuntimeError('close failed')
        with patch('backend.main.build_container', return_value=container):
            with self.assertRaisesRegex(RuntimeError, 'close failed'):
                with TestClient(app):
                    pass
        self.assertIsNone(app.state.container)
