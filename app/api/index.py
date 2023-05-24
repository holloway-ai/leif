

from redis import Redis
from redis.commands.search.field import TagField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np

def create_index(redis_connect, index_name, doc_prefix, vector_name, vector_dimensions, distance_metric='IP'):
    try:
        redis_connect.ft(index_name).info()
        redis_connect.execute_command('FT.DROPINDEX', index_name)  # Drop the existing index
    except:
        pass 

    # schema
    schema = (
        TagField("path"),                       # Tag Field Name
        VectorField(vector_name,                # Vector Field Name
                    "HNSW", 
                    {"TYPE": "FLOAT32", 
                     "DIM": vector_dimensions, 
                     "DISTANCE_METRIC": distance_metric}
        ),
    )
    # index Definition
    definition = IndexDefinition(prefix=[doc_prefix], index_type=IndexType.HASH)
    # create Index
    redis_connect.ft(index_name).create_index(fields=schema, definition=definition)

def search_vectors_knn(redis_connect, query_vector, index_name, vector_name, top_k):
    base_query = f'*=>[KNN {top_k} @{vector_name} $vector]=>{{$yield_distance_as: dist}}'
    query = Query(base_query).sort_by('dist').return_fields("id", "dist").paging(0, top_k).dialect(2)    
    try:
        results = redis_connect.ft(index_name).search(query, query_params={"vector": query_vector.tobytes()}).docs
    except Exception as e:
        print("Error calling Redis search: ", e)
        return None
    
    return results