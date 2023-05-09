from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import collections

router = APIRouter()

@router.get("/", response_model=List[schemas.SearchResult])
def search(query: str) -> Any:
    results = []

    for collection in collections:
        for document in collection.documents:
            if query.lower() in document.title.lower():
                result = schemas.SearchResult(id=document.path, # IT IS PATH FOR NOW
                                              title=document.title, 
                                              description=document.description, 
                                              path=document.path, 
                                              locale=document.localeCode)
                results.append(result)
                suggestions = []        # EMPTY FOR NOW

    return {"results": results, "suggestions": suggestions, "totalHits": len(results)+ len(suggestions)}
