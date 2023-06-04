from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.api import index
from app.api import utils

router = APIRouter()

@router.get("/", response_model=List[str])
def list_collections() -> Any:
    """
    Retrieve existing collections names.
    """
    existing_collections = [x.decode('utf-8') for x in deps.db.connection.execute_command('FT._LIST')]
    
    return existing_collections

@router.post("/", response_model=str)
def create_collection(new_collection: schemas.Collection) -> Any:
    """
    Add new empty collection.
    """
    collection_db = deps.CollectionDB(connection = deps.db.connection, 
                                      name = new_collection.name)
    index.create_index(deps.db.connection,
                       new_collection.name,
                       collection_db.get_a_prefix(),
                       utils.VECTOR_FIELD_NAME,
                       utils.VECTOR_DIMENSIONS)
    return "Index created / updated"


@router.delete("/{collection_name}", response_model=str)
def delete_collection(collection_name: str, collection_db: deps.CollectionDep) -> Any:
    """
    Delete collection.
    """
    keys_to_delete = collection_db.search_by_path( "*")
    for key in keys_to_delete:
        deps.db.connection.delete(key)

    existing_collections = [x.decode('utf-8') for x in deps.db.connection.execute_command('FT._LIST')]

    if collection_name not in existing_collections:
        raise HTTPException(status_code=404, detail="Collection not found")

    deps.db.connection.execute_command('FT.DROPINDEX', collection_name)

    return f"Collection {collection_name} deleted"