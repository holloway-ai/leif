from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import existing_collections

router = APIRouter()

@router.get("/", response_model = schemas.SearchResultFull)
def search(query: str) -> Any:   
    emptySearchResult =  schemas.SearchResult(id="", title="", description="", path="", locale="")
    results = []
    suggestions = []        # EMPTY FOR NOW

    if len(existing_collections) < 1:
        raise HTTPException(status_code=404, detail="No Collections")

    for collection_name, collection in existing_collections.items():
        if len(collection.documents) < 1:
            continue
        for document_id, document in collection.documents.items():
            if query.lower() == document.title.lower():
                result = schemas.SearchResult(
                    id=f"{collection_name}_{document_id}",  # ID IS PATH FOR NOW
                    title=document.title,
                    description=document.description,
                    path=document_id,
                    locale=document.localeCode
                )
                results.append(result)

    return schemas.SearchResultFull(
        results=results,
        suggestions=suggestions,
        totalHits=len(results) + len(suggestions)
    )

    