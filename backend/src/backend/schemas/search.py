from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    # None মানে user পছন্দ দেননি; service application-এর default নেবে।
    limit: int | None = Field(default=None, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    category: str | None = None
    document_id: str | None = Field(default=None, min_length=1)


class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    document_id: str | None = None
    source: str | None = None
    category: str | None = None
    page_number: int | None = None
    page_end: int | None = None
    chunk_index: int | None = None


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SearchResult]
