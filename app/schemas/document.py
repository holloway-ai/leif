from pydantic import BaseModel
from typing import Optional

class DocumentBase(BaseModel):
    path: Optional[str] = None
    localeCode: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    render: Optional[str] = None

class DocumentCreate(DocumentBase):
    path: str
    localeCode: str
    title: str
    content: str
    render: str

class DocumentUpdate(DocumentBase):
    pass

class DocumentInDBBase(DocumentBase):
    pass

class Document(DocumentInDBBase):
    path: str
    localeCode: str
    title: str
    content: str
    render: str