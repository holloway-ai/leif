from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import utils
from app.api import index
from app.core.config import settings

import lxml.html
import cohere
import numpy as np

from redis import Redis
from redis.commands.search.query import Query

router = APIRouter()

# Connect to Cohere API
cohere_client = cohere.Client(settings.COHERE_API_KEY)

# Set up Redis connect
redis_conn = Redis( host = settings.REDIS_HOST,
                    port = settings.REDIS_PORT,
                    password = settings.REDIS_PASSWORD)
 
# create the index
index.create_index(redis_connect = redis_conn, 
                   doc_prefix = utils.DOC_PREFIX, 
                   index_name = utils.INDEX_NAME, 
                   vector_name = utils.VECTOR_FIELD_NAME,
                   vector_dimensions =  utils.VECTOR_DIMENSIONS)

@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection_name: str) -> Any:
    """
    Get a list of document IDs in the collection.
    """
    collection = utils.get_collection_by_name(collection_name)
    return list(collection.documents.keys())

@router.post("/{collection_name}/", response_model=List[str])
def add_documents( collection_name: str, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    collection = utils.get_collection_by_name(collection_name)
    
    # instantiate and fill redis pipeline
    pipe = redis_conn.pipeline()
    for document in documents:
        # Assume that the `path` attribute is used as the document ID
        if document.path in collection.documents:
            continue
        # Update local collection tabel
        collection.documents[document.path] = document
        
        # define key
        blocks = utils.extract_info_blocks(document.render, threshold=utils.THRESHOLD)
        encoded_blocks = [ utils.encode_blocks(cohere_client,block['text']) for block in blocks ] 

        for i,vector in enumerate(encoded_blocks):
            #hash key
            document_metadata = {"path": document.path, 
                                 "title": document.title, 
                                 "tag_id": blocks[i]['tag_id'], 
                                 "chunk_num": blocks[i]['chunk_num'],
                                 "text": blocks[i]['text'],
                                 "locale": document.localeCode }
            key = utils.get_a_key(utils.DOC_PREFIX, collection_name, document, i)
            
            document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
            # HSET
            pipe.hset(key, mapping=document_metadata)
    pipe.execute()

    return list(collection.documents.keys())

@router.get("/{collection_name}/{path}", response_model=schemas.Document)
def read_document(collection_name: str, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    collection = utils.get_collection_by_name(collection_name)
    document = collection.documents.get(path)
    if document:
        return document
    raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{collection_name}/{path}", response_model=schemas.Document)
def update_document( collection_name: str, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    collection = utils.get_collection_by_name(collection_name)

    if path in collection.documents:
        collection.documents[path].localeCode = document.localeCode
        collection.documents[path].title = document.title
        collection.documents[path].description = document.description

        if document.render != collection.documents[path].render :
            keys_to_delete = utils.search_by_path(redis_conn, collection_name, path)
            for key in keys_to_delete:
                redis_conn.delete(key)
            collection.documents[path].render = document.render

        # instantiate and fill redis pipeline
        pipe = redis_conn.pipeline()
        blocks = utils.extract_info_blocks(document.render, threshold = utils.THRESHOLD)
        encoded_blocks = [ utils.encode_blocks(cohere_client,block['text']) for block in blocks ] 
        for i,vector in enumerate(encoded_blocks):
            document_metadata = {"path": path, 
                                 "title": document.title, 
                                 "tag_id": blocks[i]['tag_id'], 
                                 "chunk_num": blocks[i]['chunk_num'],
                                 "text": blocks[i]['text'],
                                  "locale": document.localeCode }
            key = utils.get_a_key(utils.DOC_PREFIX, collection_name, document, i)
            document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
            pipe.hset(key, mapping=document_metadata)
        pipe.execute()

        return collection.documents[path]
    
    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    collection = utils.get_collection_by_name(collection_name)

    if path in collection.documents:
        keys_to_delete = utils.search_by_path(redis_conn, collection_name, path)
        for key in keys_to_delete:
            redis_conn.delete(key)
        del collection.documents[path]

        return f"Document {path} deleted"

    raise HTTPException(status_code=404, detail="Document not found")