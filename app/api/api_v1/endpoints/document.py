from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import existing_collections

router = APIRouter()

def get_collection_by_name(name: str):
    """
    Return collection by name
    """
    collection = existing_collections.get(name)
    if collection:
        return collection
    raise HTTPException(status_code=404, detail="Collection not found")

@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection_name: str) -> Any:
    """
    Get a list of document IDs in the collection.
    """
    collection = get_collection_by_name(collection_name)
    return list(collection.documents.keys())

@router.post("/{collection_name}/", response_model=List[str])
def add_documents( collection_name: str, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    collection = get_collection_by_name(collection_name)
 
    # Validate and add each document to the collection
    for document in documents:
        # Assume that the `path` attribute is used as the document ID
        if document.path in collection.documents:
            continue

        collection.documents[document.path] = schemas.Document( path = document.path,
                                                                localeCode = document.localeCode,
                                                                title = document.title,
                                                                description = document.description,
                                                                render = document.render)
    return list(collection.documents.keys())

@router.get("/{collection_name}/{path}", response_model=schemas.Document)
def read_document(collection_name: str, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    collection = get_collection_by_name(collection_name)
    document = collection.documents.get(path)
    if document:
        return document
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{collection_name}/{path}", response_model=schemas.Document)
def update_document( collection_name: str, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    collection = get_collection_by_name(collection_name)

    if path in collection.documents:
        collection.documents[path].localeCode = document.localeCode
        collection.documents[path].title = document.title
        collection.documents[path].description = document.description
        collection.documents[path].render = document.render
        return collection.documents[path]

    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    collection = get_collection_by_name(collection_name)

    if path in collection.documents:
        del collection.documents[path]
        return f"Document {path} deleted"

    raise HTTPException(status_code=404, detail="Document not found")