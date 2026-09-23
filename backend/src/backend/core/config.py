"""Class 5: Central place for all app configuration.

Change the database, model, or chunk size without changing business logic.
Reading order: config → bootstrap → container → main → dependencies.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """BaseModel validates data; BaseSettings also reads environment values.

    Priority: Settings(...) argument > environment > .env > default.
    For example, INTC_CHUNK_SIZE=700 overrides the default value of 500.
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # Read .env from the server's working directory.
        env_file_encoding="utf-8",
        env_prefix="INTC_",  # chunk_size → INTC_CHUNK_SIZE: project-specific name.
        extra="ignore",  # Ignore settings used by other tools.
        populate_by_name=True,
    )

    app_name: str = "IntelliDocs API"
    app_version: str = "1.0.0"
    # AliasChoices supports legacy environment names; the first match wins.
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias=AliasChoices("INTC_QDRANT_URL", "QDRANT_URL"))
    qdrant_collection: str = Field(default="documents_v2", validation_alias=AliasChoices("INTC_QDRANT_COLLECTION", "DOCUMENTS_COLLECTION"))
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias=AliasChoices("INTC_EMBEDDING_MODEL", "EMBEDDING_MODEL_NAME"))

    # gt means >, ge means >=, and le means <=. Invalid values fail at startup.
    chunk_size: int = Field(default=500, gt=0)
    overlap_sentences: int = Field(default=1, ge=0)
    oversized_overlap: int = Field(default=50, ge=0)
    search_default_limit: int = Field(default=3, ge=1, le=20)
    search_score_threshold: float = Field(default=0.4, ge=-1.0, le=1.0, validation_alias=AliasChoices("INTC_SEARCH_SCORE_THRESHOLD", "SEARCH_SCORE_THRESHOLD"))

    # Legacy demo settings; the new runtime gets the size from the embedding.
    demo_documents_collection: str = Field(default="documents", validation_alias=AliasChoices("INTC_DEMO_DOCUMENTS_COLLECTION", "DEMO_DOCUMENTS_COLLECTION"))
    demo_vector_size: int = Field(default=3, gt=0, validation_alias=AliasChoices("INTC_DEMO_VECTOR_SIZE", "DEMO_VECTOR_SIZE"))
    embedding_vector_size: int = Field(default=384, gt=0, validation_alias=AliasChoices("INTC_EMBEDDING_VECTOR_SIZE", "EMBEDDING_VECTOR_SIZE"))

    @model_validator(mode="after")
    def validate_chunk_settings(self) -> "Settings":
        # Values can be valid alone but invalid together: size=500, overlap=700.
        # Check their relationship after field validation. Chunker also validates
        # them because it can be created without Settings.
        if self.oversized_overlap >= self.chunk_size:
            raise ValueError("oversized_overlap must be smaller than chunk_size")
        return self

    @property
    def documents_collection(self) -> str:
        """Keep legacy lesson code on the same collection."""
        return self.qdrant_collection

    @property
    def embedding_model_name(self) -> str:
        return self.embedding_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate once, then return the cached settings.

    The cache lasts for this Python process. Restart after changing .env.
    Tests can call get_settings.cache_clear() to reload the environment.
    """
    return Settings()


# Keep legacy lesson imports working; this does not load an ML model.
settings = get_settings()
