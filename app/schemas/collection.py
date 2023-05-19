from typing import Dict, List
from pydantic import BaseModel
from .document import Document

class Collection(BaseModel):
    name: str
    description: str
    #documents: Dict[str, Document]
    documents: Dict[str, str]

class CollectionCreate(BaseModel):
    name: str
    description: str