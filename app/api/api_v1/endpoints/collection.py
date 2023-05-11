from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps

from app.shared_state import existing_collections

router = APIRouter()

@router.get("/", response_model=List[str])
def list_collections() -> Any:
    """
    Retrieve existing collections names.
    """
    return list(existing_collections.keys())

@router.post("/", response_model=schemas.Collection)
def create_collection(new_collection: schemas.CollectionCreate) -> Any:
    """
    Add new empty collection.
    """
    if new_collection.name in existing_collections:
        raise HTTPException(status_code=409, detail="Collection already exists")

    collection = schemas.Collection(name=new_collection.name,
                                    description=new_collection.description,
                                    documents={}
                                    )
    existing_collections[new_collection.name] = collection
    return collection

@router.put("/{name}", response_model=schemas.Collection)
def update_collection(name: str, updated_collection: schemas.CollectionCreate) -> Any:
    if name not in existing_collections:
        raise HTTPException(status_code=404, detail="Collection not found")

    collection = existing_collections[name]
    collection.name = updated_collection.name
    collection.description = updated_collection.description

    # Update the dictionary key if the name has changed
    if name != updated_collection.name:
        existing_collections[updated_collection.name] = collection
        del existing_collections[name]

    return collection

@router.delete("/{name}", response_model= str )
def delete_collection(name: str) -> Any:
    if name not in existing_collections:
        raise HTTPException(status_code=404, detail="Collection not found")

    del existing_collections[name]

    return f"Collection {name} deleted"