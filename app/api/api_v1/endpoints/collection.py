from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.api import llm
from app.api import llm

from app.api.classes import collection


router = APIRouter()

@router.get("/", response_model=List[str])
def list_collections() -> Any:    
    return collection.list_collections()

@router.post("/", response_model=str)
def create_collection(new_collection: schemas.Collection) -> Any:
    """
    Add new empty collection.
    """
    collection_db = collection.CollectionDB(connection = deps.db.connection, name = new_collection.name)
    collection_db.create_index()
    return "Index created / updated"


@router.delete("/{collection_name}", response_model=str)
def delete_collection(collection_name: str, collection_db: collection.CollectionDep) -> Any:
    """
    Delete collection.
    """
    existing_collections = collection.list_collections()
    
    if collection_name not in existing_collections:
        raise HTTPException(status_code=404, detail="Collection not found")    

    return collection_db.delete_collection()