from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import utils
from app.api import index
from app.api import Depends

from app.shared_state import existing_collections
from app.core.config import settings  # pylint: disable=C0415

router = APIRouter()

import lxml.html
import numpy as np


@router.get("/", response_model = schemas.SearchResultFull)
def search(query: str) -> Any:   
    results = []
    suggestions = []        # EMPTY FOR NOW

    if len(existing_collections) < 1:
        raise HTTPException(status_code=404, detail="No Collections")

    query_embedding = utils.encode_blocks(Depends.embedder.connection, query )

    collection_list = [x.decode('utf-8') for x in Depends.db.connection.execute_command('FT._LIST')]

    for collection in collection_list:
        redis_search_results = index.search_vectors_knn(redis_connect =Depends.db.connection, 
                                                        query_vector = query_embedding, 
                                                        index_name = collection, 
                                                        vector_name = utils.VECTOR_FIELD_NAME, 
                                                        top_k=4)
        for redis_doc in redis_search_results:

            redis_dict = Depends.db.connection.hgetall( redis_doc['id'].encode('utf-8') )
            redis_path = redis_dict['path'.encode('utf-8')].decode('utf-8')
            redis_tag = redis_dict['tag_id'.encode('utf-8')].decode('utf-8')

            result = schemas.SearchResult(
                        id=f"{redis_path}_{redis_tag}", 
                        title = redis_dict['title'.encode('utf-8')],
                        description = redis_dict['text'.encode('utf-8')],
                        path = f"{redis_path}#{redis_tag}",
                        locale = redis_dict['locale'.encode('utf-8')]    
                    )
            results.append(result)

    return schemas.SearchResultFull(results=results,
                                    suggestions=suggestions,
                                    totalHits=len(results) + len(suggestions))

