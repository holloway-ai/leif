from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import existing_collections

router = APIRouter()

def get_collection_by_name(name: str):
    """ return collection by name"""
    for collection in existing_collections:
        if collection.name == name:
            return collection
    raise HTTPException(status_code=404, detail="Collection not found")

@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection_name: str) -> Any:
    """
    Get a list of documents in the collection.
    """
    collection = get_collection_by_name(collection_name)
    return collection.ids


@router.post("/{collection_name}/", response_model=List[schemas.Document])
def add_documents( collection_name: str, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    collection = get_collection_by_name(collection_name)
 
    # Validate and add each document to the collection
    for document in documents:
        # Assume that the `path` attribute is used as the document ID
        if document.path in collection.ids:
            continue

        collection.documents.append( schemas.Document( path = document.path,
                                                       localeCode = document.localeCode,
                                                       title = document.title,
                                                       description = document.description,
                                                       render = document.render))
        collection.ids.append( document.path )

    return collection.documents

@router.get("/{collection_name}/{path}", response_model=schemas.Document)
def read_document(collection_name: str, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    collection = get_collection_by_name(collection_name)

    for document in collection.documents:
        # Assume that the `path` attribute is used as the document ID
        if document.path == path:
            return document
        
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{collection_name}/{path}", response_model=schemas.Document)
def update_document( collection_name: str, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    collection = get_collection_by_name(collection_name)

    for current_document in collection.documents:
        if current_document.path == path:
            current_document.localeCode = document.localeCode
            current_document.title = document.title
            current_document.description = document.description
            current_document.render = document.render
            return current_document

    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    collection = get_collection_by_name(collection_name)
    for index, current_document in enumerate(collection.documents):
        if current_document.path == path:
            del collection.documents[index]
            del collection.ids[index]
            return f"Document {path} deleted"

    raise HTTPException(status_code=404, detail="Document not found")