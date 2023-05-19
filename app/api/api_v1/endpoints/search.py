from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import deps
from app.shared_state import existing_collections
from app.core.config import settings  # pylint: disable=C0415

router = APIRouter()

from redis import Redis
from redis.commands.search.field import VectorField
from redis.commands.search.field import TextField
from redis.commands.search.field import TagField
from redis.commands.search.query import Query
from redis.commands.search.result import Result

# Encode query using Cohere
def encode_query(query): 
    return cohere.embed('baseline-embed', texts=[query])[0]

# Run semantic search
def search(query, top_k=3):
    encoded_query = encode_query(query)
    encoded_query_bytes = encoded_query.tobytes()

    search_result = search_client.search(
        Query("").return_fields(["document_id", "block_id"]).vector_similarity(vector_field_name, encoded_query_bytes).limit(0, top_k)
    )
    return [(res.document['document_id'], res.document['block_id']) for res in search_result.docs]

def load_vectors(client: Redis, product_metadata, vector_dict, vector_field_name):
    p = client.pipeline(transaction=False)
    for index in product_metadata.keys():    
        #hash key
        key='product:'+ str(index)+ ':' + product_metadata[index]['primary_key']
        
        #hash values
        item_metadata = product_metadata[index]
        item_keywords_vector = vector_dict[index].astype(np.float32).tobytes()
        item_metadata[vector_field_name]=item_keywords_vector
        
        # HSET
        p.hset(key,mapping=item_metadata)
            
    p.execute()

def create_flat_index (redis_conn,vector_field_name,number_of_vectors, vector_dimensions=512, distance_metric='L2'):
    redis_conn.ft().create_index([
        VectorField(vector_field_name, "FLAT", {"TYPE": "FLOAT32", "DIM": vector_dimensions, "DISTANCE_METRIC": distance_metric, "INITIAL_CAP": number_of_vectors, "BLOCK_SIZE":number_of_vectors }),
        TagField("product_type"),
        TextField("item_name"),
        TextField("item_keywords"),
        TagField("country")        
    ])


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

    