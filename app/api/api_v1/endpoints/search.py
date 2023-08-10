from typing import Any

from fastapi import APIRouter, HTTPException
from app import schemas

from app.api.classes import collection as collection_class

router = APIRouter()

@router.get("/{collection_name}/", response_model = schemas.SearchResultFull)
def search(collection: collection_class.CollectionDep, query: str) -> Any:
    """
    Semantic search in the collection. Question+Answer with links
    """
    return collection.full_search_doc(query)

