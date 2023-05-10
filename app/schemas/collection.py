from typing import List
from pydantic import BaseModel
from .document import Document

class Collection(BaseModel):
    name: str
    description: str
    documents: List[Document]
    ids: List[str] # ids of docs in collection

class CollectionCreate(BaseModel):
    name: str
    description: str