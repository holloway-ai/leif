from typing import List
from pydantic import BaseModel


class Document(BaseModel):
    id: str 
    path: str 
    locale: str
    title: str
    description: str
    render: str  # This will represent the HTML of the page as a string

class DocumentUpdate(BaseModel):
    path: str 
    locale: str
    title: str
    description: str
    render: str  # This will represent the HTML of the page as a string