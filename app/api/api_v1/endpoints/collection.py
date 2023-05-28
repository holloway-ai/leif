from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import Depends
from app.api import index
from app.api import utils


router = APIRouter()

@router.get("/", response_model=List[str])
def list_collections() -> Any:
    """
    Retrieve existing collections names.
    """
    existing_collections = [x.decode('utf-8') for x in Depends.db.connection.execute_command('FT._LIST')]
    
    return existing_collections

@router.post("/", response_model=str)
def create_collection(new_collection: schemas.CollectionCreate) -> Any:
    """
    Add new empty collection.
    """
    index.create_index( Depends.db.connection,
                        new_collection.name, 
                        utils.get_a_prefix(new_collection.name),
                        utils.VECTOR_FIELD_NAME, 
                        utils.VECTOR_DIMENSIONS)
    
    return "Index created / updated"

@router.delete("/{name}", response_model= str )
def delete_collection(name: str) -> Any:
    """
    Delete collection.
    """    
    keys_to_delete = utils.search_by_path(Depends.db.connection, name, "*")
    for key in keys_to_delete:
        Depends.db.connection.delete(key)
    
    existing_collections = [x.decode('utf-8') for x in Depends.db.connection.execute_command('FT._LIST')]

    if name not in existing_collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    Depends.db.connection.execute_command('FT.DROPINDEX', name)

    return f"Collection {name} deleted"