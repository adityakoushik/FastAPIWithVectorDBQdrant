"""Composition root: কোন কাজের জন্য কোন object লাগবে, এখানে জুড়ে দিই।

রান্নার আগে উপকরণ সাজানোর মতো: startup-এ তৈরি → request-এ ব্যবহার।
Services নিজেরা model/database বানায় না; আমরা তাদের হাতে দিয়ে দিই।
এই হাতে তুলে দেওয়াই Dependency Injection (DI)।
"""

from contextlib import ExitStack

from qdrant_client import QdrantClient

from backend.chunkers.sentence_aware_chunker import SentenceAwareChunker
from backend.controllers.document_controller import DocumentController
from backend.controllers.search_controller import SearchController
from backend.core.config import Settings
from backend.core.container import AppContainer
from backend.nlp.spacy_sentence_splitter import SpacySentenceSplitter
from backend.parsers.pdf_parser import PdfParser
from backend.repositories.qdrant_vector_repository import QdrantVectorRepository
from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService
from backend.services.search_service import SearchService


def build_container(settings: Settings) -> AppContainer:
    """প্রতি application lifespan-এ একবার dependency graph বানাও।

    একাধিক worker process হলে প্রত্যেকটির নিজস্ব model ও container হয়।
    Client তৈরি মানেই database/collection ready প্রমাণিত নয়;
    collection-এর startup validation পরের lesson-এর কাজ।
    """
    with ExitStack() as cleanup:
        qdrant_client = QdrantClient(url=settings.qdrant_url)
        # পরের ধাপে model load ব্যর্থ হলেও খোলা client বন্ধ হবে।
        cleanup.callback(qdrant_client.close)
        parser = PdfParser()
        sentence_splitter = SpacySentenceSplitter()
        chunker = SentenceAwareChunker(
            sentence_splitter=sentence_splitter,
            chunk_size=settings.chunk_size,
            overlap_sentences=settings.overlap_sentences,
            oversized_overlap=settings.oversized_overlap,
        )
        embedding_service = EmbeddingService(model_name=settings.embedding_model)
        vector_repository = QdrantVectorRepository(
            client=qdrant_client, collection_name=settings.qdrant_collection,
        )
        # একই model ও repository দুই service-কে দিচ্ছি। Upload ও search-এর
        # জন্য দুবার SentenceTransformer load হচ্ছে না।
        document_service = DocumentService(
            parser=parser, chunker=chunker,
            embedding_service=embedding_service,
            vector_repository=vector_repository,
        )
        search_service = SearchService(
            embedding_service=embedding_service,
            vector_repository=vector_repository,
            default_limit=settings.search_default_limit,
            default_score_threshold=settings.search_score_threshold,
        )
        container = AppContainer(
            document_controller=DocumentController(document_service),
            search_controller=SearchController(search_service),
            qdrant_client=qdrant_client,
        )
        # সফল হলে cleanup-এর দায়িত্ব main.py-এর lifespan পায়।
        cleanup.pop_all()
        return container
