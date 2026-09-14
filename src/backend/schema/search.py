from pydantic import BaseModel

# Here SearchRequest is the Schema or Structure of request body
class SearchRequest(BaseModel):
    query: str
    limit: int = 3