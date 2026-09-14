from pydantic import BaseModel

class DocumentCreate(BaseModel):
    text: str
    source: str | None = None
    category: str | None = None