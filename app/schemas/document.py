from typing import List
from pydantic import BaseModel


class Document(BaseModel):
    path: str # for now use as an index
    localeCode: str
    title: str
    description: str
    render: str  # This will represent the HTML of the page as a string

class DocumentUpdate(BaseModel):
    localeCode: str
    title: str
    description: str
    render: str  # This will represent the HTML of the page as a string