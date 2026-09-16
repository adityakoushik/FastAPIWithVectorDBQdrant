from pydantic import BaseModel


class DocumentPage(BaseModel):
    page_number: int
    text: str