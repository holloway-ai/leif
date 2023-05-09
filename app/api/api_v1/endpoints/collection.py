from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps

from app.shared_state import collections

router = APIRouter()

@router.get("/", response_model=List[schemas.Collection])
def list_collections() -> Any:
    """
    Retrieve collections.
    """
    return collections

@router.post("/", response_model=schemas.Collection)
def create_collection(new_collection: schemas.CollectionCreate) -> Any:
    for collection in collections:
        if collection.id == new_collection.id:
            raise HTTPException(status_code=409, detail="Collection already exists")

    collection = schemas.Collection(id=new_collection.id, title=new_collection.title, description=new_collection.description, documents=[])
    collections.append(collection)
    return collection

@router.put("/{id}", response_model=schemas.Collection)
def update_collection(id: str, updated_collection: schemas.CollectionUpdate) -> Any:
    for collection in collections:
        if collection.id == id:
            collection.title = updated_collection.title or collection.title
            collection.description = updated_collection.description or collection.description
            return collection

    raise HTTPException(status_code=404, detail="Collection not found")

@router.get("/{id}", response_model=schemas.Collection)
def read_collection(id: str) -> Any:
    for collection in collections:
        if collection.id == id:
            return collection

    raise HTTPException(status_code=404, detail="Collection not found")

@router.delete("/{id}", response_model=schemas.Collection)
def delete_collection(id: str) -> Any:
    for collection in collections:
        if collection.id == id:
            collections.remove(collection)
            return collection

    raise HTTPException(status_code=404, detail="Collection not found")