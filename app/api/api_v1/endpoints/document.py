from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import utils
from app.api import Depends


import numpy as np

from redis import Redis
from redis.commands.search.query import Query

router = APIRouter()


@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection_name: str) -> Any:
    """
    Get a list of document IDs in the collection.
    """
    return utils.search_by_path(Depends.db.connection, collection_name, "*")

@router.post("/{collection_name}/", response_model=str)
def add_documents( collection_name: str, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    # instantiate and fill redis pipeline
    pipe = Depends.db.connection.pipeline()
    for document in documents:
        # define key
        blocks = utils.extract_info_blocks(document.render, threshold=utils.THRESHOLD)
        encoded_blocks = [ utils.encode_blocks(Depends.embedder.connection,block['text']) for block in blocks ] 
        for i,vector in enumerate(encoded_blocks):
            #hash key
            document_metadata = {"path": document.path, 
                                 "title": document.title, 
                                 "tag_id": blocks[i]['tag_id'], 
                                 "chunk_num": blocks[i]['chunk_num'],
                                 "text": blocks[i]['text'],
                                 "locale": document.localeCode }
            key = utils.get_a_key(collection_name, document.path, i)
            
            document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
            # HSET
            pipe.hset(key, mapping=document_metadata)

    pipe.execute()

    return 'Documents added'

@router.get("/{collection_name}/{path}", response_model=List[str])
def read_document(collection_name: str, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    search_list = utils.search_by_path(Depends.db.connection, collection_name, path)
    if len(search_list) > 0:
        return  [Depends.db.connection.hgetall( search_result )[b'text'] for search_result in search_list ]
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.put("/{collection_name}/{path}", response_model=List[str])
def update_document( collection_name: str, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    keys_to_delete = utils.search_by_path(Depends.db.connection, collection_name, path)

    if len(keys_to_delete) < 1:
        raise HTTPException(status_code=404, detail="Document not found")

    for key in keys_to_delete:
        Depends.db.connection.delete(key)

    # instantiate and fill redis pipeline
    pipe = Depends.db.connection.pipeline()
    blocks = utils.extract_info_blocks(document.render, threshold = utils.THRESHOLD)
    encoded_blocks = [ utils.encode_blocks(Depends.embedder.connection,block['text']) for block in blocks ] 
    for i,vector in enumerate(encoded_blocks):
        document_metadata = {"path": path, 
                            "title": document.title, 
                             "tag_id": blocks[i]['tag_id'], 
                             "chunk_num": blocks[i]['chunk_num'],
                             "text": blocks[i]['text'],
                              "locale": document.localeCode }
        key = utils.get_a_key(collection_name, path, i)
        document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
        pipe.hset(key, mapping=document_metadata)
    pipe.execute()

    search_list = utils.search_by_path(Depends.db.connection, collection_name, path)
    
    return [Depends.db.connection.hgetall( search_result )[b'text'] for search_result in search_list ]


@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection_name: str, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    keys_to_delete = utils.search_by_path(Depends.db.connection, collection_name, path)
    if len(keys_to_delete) < 1:
        raise HTTPException(status_code=404, detail="Document not found")

    for key in keys_to_delete:
        Depends.db.connection.delete(key)

        return f"Document {path} deleted"
