from typing import Any, List
from fastapi import APIRouter, HTTPException, Depends
from app import schemas
from app.api import utils
from app.api import deps


import numpy as np

from redis import Redis
from redis.commands.search.query import Query

router = APIRouter()


@router.get("/{collection_name}/", response_model=List[str])
def list_documents(collection:  deps.CollectionDep) -> Any:
    keys = [key for key in collection.connection.scan_iter(f"{collection.name}*")]
    # Check if the list is empty
    if len(keys) < 1:
        raise HTTPException(status_code=404, detail="No documents")
    # Extract document keys from keys
    document_keys = [key.decode('utf-8').split(":")[1] for key in keys]
    # Get unique document keys
    unique_document_keys = list(set(document_keys))
    return unique_document_keys

#@router.get("/{collection_name}/", response_model=List[str])
#def list_documents(collection:  deps.CollectionDep) -> Any:
#    pipe = collection.connection.pipe()
#    return collection.name

@router.post("/{collection_name}/", response_model=str)
def add_documents( collection: deps.CollectionDep, documents: List[schemas.Document]) -> Any:
    """
    Dump LIST of new documents to a collection.
    """
    # instantiate and fill redis pipeline
    pipe = deps.db.connection.pipeline()
    for document in documents:
        # define key
        blocks = utils.extract_info_blocks(document.render, threshold=utils.THRESHOLD)
        encoded_blocks = [ utils.encode_blocks(deps.db.embedding,block['text']) for block in blocks ] 
        for i,vector in enumerate(encoded_blocks):
            #hash key
            document_metadata = {"path": document.path, 
                                 "title": document.title, 
                                 "render_id": blocks[i]['render_id'], 
                                 "chunk_num": blocks[i]['chunk_num'],
                                 "text": blocks[i]['text'],
                                 "content": blocks[i]['content'],
                                 "locale": document.localeCode }

            key = collection.get_a_key(document.path, i)
            
            document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
            # HSET
            pipe.hset(key, mapping=document_metadata)

    pipe.execute()

    return 'Documents added'

@router.get("/{collection_name}/{path}", response_model=List[str])
def read_document(collection: deps.CollectionDep, path: str) -> Any:
    """
    Get a specific document in the collection by its path.
    """
    search_list = collection.search_by_path( path)
    if len(search_list) > 0:
        return  [deps.db.connection.hgetall( search_result )[b'text'] for search_result in search_list ]
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.put("/{collection_name}/{path}", response_model=List[str])
def update_document( collection: deps.CollectionDep, path: str, document: schemas.DocumentUpdate) -> Any:
    """
    Update a document in a collection.
    """
    keys_to_delete = collection.search_by_path(path)

    if len(keys_to_delete) < 1:
        raise HTTPException(status_code=404, detail="Document not found")

    for key in keys_to_delete:
        deps.db.connection.delete(key)

    # instantiate and fill redis pipeline
    pipe = deps.db.connection.pipeline()
    blocks = utils.extract_info_blocks(document.render, threshold = utils.THRESHOLD)
    encoded_blocks = [ utils.encode_blocks(deps.db.embedding,block['text']) for block in blocks ] 
    for i,vector in enumerate(encoded_blocks):
        document_metadata = {"path": path, 
                            "title": document.title, 
                             "render_id": blocks[i]['render_id'], 
                             "chunk_num": blocks[i]['chunk_num'],
                             "text": blocks[i]['text'],
                             "content": blocks[i]['content'],
                             "locale": document.localeCode }
        key = collection.get_a_key( path, i)
        document_metadata[utils.VECTOR_FIELD_NAME] = np.array(vector).astype(np.float32).tobytes()
        pipe.hset(key, mapping=document_metadata)
    pipe.execute()

    search_list = collection.search_by_path(path)
    
    return [deps.db.connection.hgetall( search_result )[b'text'] for search_result in search_list ]


@router.delete("/{collection_name}/{path}", response_model = str)
def delete_document(collection: deps.CollectionDep, path: str) -> Any:
    """
    Delete a document in a collection.
    """
    keys_to_delete = collection.search_by_path(path)
    if len(keys_to_delete) < 1:
        raise HTTPException(status_code=404, detail="Document not found")

    for key in keys_to_delete:
        deps.db.connection.delete(key)
    
    return f"Document {path} deleted"
