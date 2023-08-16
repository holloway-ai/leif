from typing import List, Optional, Dict
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    title: str
    path: str
    text: str

class SearchResultDocument(BaseModel):
    title: str
    path: str
    text_blocks: List[str]

class QnA(BaseModel):
    question: str
    answer: Optional[str] = None
    links: List[str]

class SearchResultFull(BaseModel):
    qnas: List[QnA]
    qnas_results: List[SearchResultDocument]
    query_results: List[SearchResultDocument]
