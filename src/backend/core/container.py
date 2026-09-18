"""Container মানে তৈরি করা জিনিস রাখার বাক্স; এটি Docker container নয়।"""

from dataclasses import dataclass

from qdrant_client import QdrantClient

from backend.controllers.document_controller import DocumentController
from backend.controllers.search_controller import SearchController


@dataclass
class AppContainer:
    """dataclass আমাদের __init__ বানায়; আমরা শুধু কী রাখব লিখি।

    Controllers-এর ভিতরে services, তাদের ভিতরে model/repository থাকে।
    Client সরাসরিও রাখছি, যাতে shutdown-এ connection বন্ধ করা যায়।
    """

    document_controller: DocumentController
    search_controller: SearchController
    qdrant_client: QdrantClient
