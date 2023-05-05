from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException


from app import schemas
from app.api import deps

router = APIRouter()

fake_db = [schemas.Collection(name="joan", description="Only implemented collection")]


@router.get("/", response_model=List[schemas.Collection])
def list_collections() -> Any:
    """
    Retrieve items.
    """
    return fake_db


@router.post("/", response_model=schemas.Collection)
def create_collection(
    new_collection: schemas.CollectionCreate,
) -> Any:
    """
    Create new collection.
    """
    if new_collection.name in [collection.name for collection in fake_db]:
        raise HTTPException(status_code=409, detail="Collection already exists")
    else:
        raise HTTPException(status_code=501, detail="Not implemented")

    return fake_db[0]


@router.put("/{name}", response_model=schemas.Collection)
def update_item(
    updated_collection: schemas.CollectionUpdate,
) -> Any:
    """
    Update an collection.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{name}", response_model=schemas.Collection)
def read_item(
    name: str,
) -> Any:
    """
    Get collection by name.
    """
    for collection in fake_db:
        if collection.name == name:
            return collection

    raise HTTPException(status_code=404, detail="Collection not found")


@router.delete("/{name}", response_model=schemas.Collection)
def delete_item(
    name: str,
) -> Any:
    """
    Delete an item.
    """
    raise HTTPException(status_code=501, detail="Not implemented")
