from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import collections

router = APIRouter()

@router.post("/")
def create_document(collection_name: str, new_document: schemas.DocumentCreate) -> Any:
    """
    Create a new document in a collection.
    """
    collection = next((c for c in collections if c.name == collection_name), None)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if any(document.path == new_document.path for document in collection.documents):
        raise HTTPException(status_code=409, detail="Document already exists")

    document = schemas.Document(**new_document.dict())
    collection.documents.append(document)
    return document

@router.get("/{path}", response_model=schemas.Document)
def read_document(collection_name: str, path: str) -> Any:
    """
    Get document by path.
    """
    collection = next((c for c in collections if c.name == collection_name), None)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    document = next((d for d in collection.documents if d.path == path), None)
    if document:
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{path}")
def update_document(collection_name: str, path: str, updated_document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    collection = next((c for c in collections if c.name == collection_name), None)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    document = next((d for d in collection.documents if d.path == path), None)
    if document:
        document_data = updated_document.dict(exclude_unset=True)
        for key, value in document_data.items():
            setattr(document, key, value)
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{path}")
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    collection = next((c for c in collections if c.name == collection_name), None)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    document = next((d for d in collection.documents if d.path == path), None)
    if document:
        collection.documents.remove(document)
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")