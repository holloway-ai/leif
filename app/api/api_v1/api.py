from fastapi import APIRouter

from .endpoints import collection, search, document

api_router = APIRouter()
api_router.include_router(collection.router, prefix="/collections", tags=["collections"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(document.router, prefix="/documents", tags=["documents"])
