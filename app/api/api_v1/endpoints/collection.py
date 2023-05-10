from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps

from app.shared_state import existing_collections

router = APIRouter()

@router.get("/", response_model=List[schemas.Collection])
def list_collections() -> Any:
    """
    Retrieve existing_collections.
    """
    return existing_collections

@router.post("/", response_model=schemas.Collection)
def create_collection(new_collection: schemas.CollectionCreate) -> Any:
    for collection in existing_collections:
        if collection.name == new_collection.name:
            raise HTTPException(status_code=409, detail="Collection already exists")
        
    collection = schemas.Collection(name=new_collection.name,
                                    description=new_collection.description,
                                    documents=[],
                                    ids=[])
    existing_collections.append(collection)
    return collection

@router.put("/{name}", response_model=schemas.Collection)
def update_collection(name: str, updated_collection: schemas.CollectionCreate) -> Any:
    for collection in existing_collections:
        if collection.name == name:
            collection.name = updated_collection.name
            collection.description = updated_collection.description
            return collection
    raise HTTPException(status_code=404, detail="Collection not found")

@router.delete("/{name}", response_model=schemas.Collection)
def delete_collection(name: str) -> Any:
    for collection in existing_collections:
        if collection.name == name:
            existing_collections.remove(collection)
            return collection
    raise HTTPException(status_code=404, detail="Collection not found")