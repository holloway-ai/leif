from typing import List, Optional, Dict
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    title: str
    path: str

class QnA (BaseModel):
    question: str
    answer: Optional[str] = None
    links: Optional[str] = None

class SearchResultFull(BaseModel):
    qnas: Dict[str,QnA] = {}
    results: Dict[str,SearchResult] # answers reference results by id , witch is key of dict
    ordered_refs: Optional[List[str]] = None
