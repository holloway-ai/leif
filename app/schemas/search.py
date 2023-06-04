from typing import List, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    path: str
    locale: str

class SearchResultFull(BaseModel):
    results: List[SearchResult]
    answers: List[str]
    links: List[str]
    questions: List[str]
    totalHits: int