from typing import List, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    path: str
    locale: str

