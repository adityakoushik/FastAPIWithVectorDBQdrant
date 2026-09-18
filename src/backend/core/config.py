"""Class 5: app চালানোর সব পছন্দ (configuration) রাখার এক জায়গা।

Database কোথায়, model কোনটি, chunk কত বড়—এগুলো বদলাতে business logic
পাল্টাতে হবে না। পড়ার ক্রম: config → bootstrap → container → main → dependencies।
"""

from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """BaseModel data যাচাই করে; BaseSettings environment থেকেও data আনে।

    সাধারণ priority: Settings(...) argument > environment > .env > default।
    যেমন INTC_CHUNK_SIZE=700 দিলে নিচের 500-এর বদলে 700 ব্যবহার হবে।
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # যে folder থেকে server চালাও, তার .env পড়বে।
        env_file_encoding="utf-8",
        env_prefix="INTC_",  # chunk_size → INTC_CHUNK_SIZE: project-এর নিজস্ব নাম।
        extra="ignore",  # .env-এ অন্য tool-এর setting থাকলে বাদ দাও।
        populate_by_name=True,
    )

    app_name: str = "IntelliDocs API"
    app_version: str = "1.0.0"
    # AliasChoices পুরোনো lesson-এর environment নামও নেয়। প্রথম নামটি জেতে।
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias=AliasChoices("INTC_QDRANT_URL", "QDRANT_URL"))
    qdrant_collection: str = Field(default="documents_v2", validation_alias=AliasChoices("INTC_QDRANT_COLLECTION", "DOCUMENTS_COLLECTION"))
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", validation_alias=AliasChoices("INTC_EMBEDDING_MODEL", "EMBEDDING_MODEL_NAME"))

    # gt মানে >, ge মানে >=, le মানে <=। -500 character-এর chunk অর্থহীন;
    # ভুল setting নিয়ে চলার বদলে app শুরুতেই জানাবে (fail fast)।
    chunk_size: int = Field(default=500, gt=0)
    overlap_sentences: int = Field(default=1, ge=0)
    oversized_overlap: int = Field(default=50, ge=0)
    search_default_limit: int = Field(default=3, ge=1, le=20)
    search_score_threshold: float = Field(default=0.4, ge=-1.0, le=1.0, validation_alias=AliasChoices("INTC_SEARCH_SCORE_THRESHOLD", "SEARCH_SCORE_THRESHOLD"))

    # পুরোনো demo lesson-এর settings; নতুন runtime embedding থেকে size পায়।
    demo_documents_collection: str = Field(default="documents", validation_alias=AliasChoices("INTC_DEMO_DOCUMENTS_COLLECTION", "DEMO_DOCUMENTS_COLLECTION"))
    demo_vector_size: int = Field(default=3, gt=0, validation_alias=AliasChoices("INTC_DEMO_VECTOR_SIZE", "DEMO_VECTOR_SIZE"))
    embedding_vector_size: int = Field(default=384, gt=0, validation_alias=AliasChoices("INTC_EMBEDDING_VECTOR_SIZE", "EMBEDDING_VECTOR_SIZE"))

    @model_validator(mode="after")
    def validate_chunk_settings(self) -> "Settings":
        # আলাদা value ঠিক হলেও জোড়াটি ভুল হতে পারে: size=500, overlap=700।
        # after: field-এর validation শেষে তাদের সম্পর্ক দেখো। Chunker-এর
        # validation-ও থাকবে, কারণ তাকে Settings ছাড়াও বানানো যায়।
        if self.oversized_overlap >= self.chunk_size:
            raise ValueError("oversized_overlap must be smaller than chunk_size")
        return self

    @property
    def documents_collection(self) -> str:
        """পুরোনো lesson-এর code-ও একই collection-এর নাম পাবে।"""
        return self.qdrant_collection

    @property
    def embedding_model_name(self) -> str:
        return self.embedding_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """প্রথম call-এ পড়ো ও যাচাই করো; পরের call-এ একই object ফেরত দাও।

    Cache এই Python process-এর মধ্যে থাকে। .env বদলালে server restart করো।
    Test-এ নতুন environment পড়াতে get_settings.cache_clear() করা যায়।
    """
    return Settings()


# পুরোনো lesson-এর imports সচল রাখে; এটি কোনো ML model load করে না।
settings = get_settings()
