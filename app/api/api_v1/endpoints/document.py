import numpy as np
from redis import Redis
from redis.commands.search.query import Query
from typing import Any, List
from fastapi import APIRouter, HTTPException, Depends

from app import schemas
from app.api import llm
from app.api import deps
from app.api.classes import document as document_class
from app.api.classes import collection as collection_class

router = APIRouter()


@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection:  collection_class.CollectionDep) -> Any:
    """
    List existing documents.
    """ 
    return collection.list_documents()

@router.get("/{collection_name}/{path}", response_model=List[str])
def read_document(collection: collection_class.CollectionDep, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    document_text = collection.read_document(path)
    if document_text == "Document not found":
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_text
    
@router.post("/{collection_name}/", response_model=str)
def add_documents( collection: collection_class.CollectionDep, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    notification = collection.add_documents( documents )
    if notification == "Documents already exist":
        raise HTTPException(status_code=404, detail="Documents already exist")
    
    return notification

@router.put("/{collection_name}/{path}", response_model = str )
def update_document( collection: collection_class.CollectionDep, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    notification = collection.update_document( path, document)
    if notification == "Document not found":
        raise HTTPException(status_code=404, detail="Document not found")

    return notification


@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection: collection_class.CollectionDep, path: str) -> Any:
    """
    Delete a document in a collection.
    """   
    notification = collection.delete_document(path)
    if notification == "Document not found":
        raise HTTPException(status_code=404, detail="Document not found")

    return notification 

