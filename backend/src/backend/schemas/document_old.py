from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    text: str
    source: str | None = None
    category: str | None = None


# Here SearchRequest is the Schema or Structure of request body.
class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=3, ge=1, le=10)
    category: str | None = None
