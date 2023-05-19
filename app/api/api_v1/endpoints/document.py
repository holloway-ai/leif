from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps

from app.shared_state import existing_collections
from app.core.config import settings

import lxml.html
import cohere

from redis import Redis


router = APIRouter()

# Connect to Cohere API
co = cohere.Client(settings.COHERE_API_KEY)

# Set up Redis connect
redis_conn = Redis( host = settings.REDIS_CONNECT.host,
                    port=settings.REDIS_CONNECT.port,
                    password=settings.REDIS_CONNECT.password)

# Function to split document into blocks
def split_into_blocks(document_render):
    html = lxml.html.fromstring(document_render)
    return [p.replace("\n", "") for p in html.xpath('//p/text()')]

# Function to encode blocks using Cohere
def encode_blocks(blocks):
    return co.embed(texts=blocks,  model='baseline-embed', truncate='LEFT').embeddings

def get_collection_by_name(name: str):
    """
    Return collection by name
    """
    collection = existing_collections.get(name)
    if collection:
        return collection
    raise HTTPException(status_code=404, detail="Collection not found")

@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection_name: str) -> Any:
    """
    Get a list of document IDs in the collection.
    """
    collection = get_collection_by_name(collection_name)
    return list(collection.documents.keys())

@router.post("/{collection_name}/", response_model=List[str])
def add_documents( collection_name: str, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    collection = get_collection_by_name(collection_name)
 
    # Validate and add each document to the collection
    for document in documents:
        # Assume that the `path` attribute is used as the document ID
        if document.path in collection.documents:
            continue

        collection.documents[document.path] = ""
        
    p = redis_conn.pipeline(transaction=False)
    for document in documents:   
        blocks = split_into_blocks(document.render)
        encoded_blocks = encode_blocks(blocks)
        for i in range(len(encoded_blocks)):
            #hash key
            key = f"{collection_name}:{document.path}:{str(i)}"
            p.set(key, np.array(encoded_blocks[i]).astype(np.float32).tobytes())
            
    p.execute()

    return list(collection.documents.keys())

@router.get("/{collection_name}/{path}", response_model=schemas.Document)
def read_document(collection_name: str, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    collection = get_collection_by_name(collection_name)
    document = collection.documents.get(path)
    if document:
        return document
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{collection_name}/{path}", response_model=schemas.Document)
def update_document( collection_name: str, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    collection = get_collection_by_name(collection_name)

    if path in collection.documents:
        collection.documents[path].localeCode = document.localeCode
        collection.documents[path].title = document.title
        collection.documents[path].description = document.description
        collection.documents[path].render = document.render
        return collection.documents[path]

    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    collection = get_collection_by_name(collection_name)

    if path in collection.documents:
        del collection.documents[path]
        return f"Document {path} deleted"

    raise HTTPException(status_code=404, detail="Document not found")