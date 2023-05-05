from fastapi import APIRouter

from app.api.api_v1.endpoints import  collection, document, search

api_router = APIRouter()

api_router.include_router(collection.router, prefix="/collection", tags=["collection"])
api_router.include_router(document.router, prefix="/document", tags=["document"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
