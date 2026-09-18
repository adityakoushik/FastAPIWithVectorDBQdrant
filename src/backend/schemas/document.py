from pydantic import BaseModel


class DocumentPage(BaseModel):
    page_number: int
    text: str


class DocumentChunk(BaseModel):
    chunk_index: int
    page_number: int
    page_end: int | None = None
    text: str
