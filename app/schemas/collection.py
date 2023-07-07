from typing import Dict, List, Optional
from pydantic import BaseModel
from .document import Document

class Collection(BaseModel):
    name: str
    description: Optional[str] = None