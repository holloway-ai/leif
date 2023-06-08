from redis.commands.search.field import TagField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np
from typing import Any, List, Annotated, Optional, Dict

from typing import List
from app.api import deps, llm
from app.api.classes import document as document_class
from app import schemas

from fastapi import Depends
from redis import Redis


class CollectionDB():
    def __init__(self, name: str, connection: Redis = deps.db.connection):
        self.connection = connection
        self.name = name
        self.VECTOR_FIELD_NAME = 'encoded_text_block'
        self.VECTOR_DIMENSIONS = llm.VECTOR_DIMENSIONS
        self.distance_metric='IP'

    def get_prefix(self):
        return f"{self.name}"
    
    def get_key(self, document_key, block_num):
        return f"{self.get_prefix()}:{str(document_key)}:{str(block_num)}"
        
    def search_by_path(self, tag):
        cursor = 0
        results = []
        while True:
            cursor, keys = self.connection.scan(cursor, match = self.get_key(tag, "*") )
            for key in keys:
                results.append(key)
            if cursor == 0:
                break
        return results

    def create_index( self ):
        try:
            self.connection.ft(self.name).info()
            self.connection.execute_command('FT.DROPINDEX', self.name)  # Drop the existing index
        except:
            pass 
        # schema
        schema = (  TagField("path"),                       # Tag Field Name
                    VectorField(self.VECTOR_FIELD_NAME,     # Vector Field Name
                    "HNSW", 
                    {"TYPE": "FLOAT32", 
                    "DIM": self.VECTOR_DIMENSIONS, 
                    "DISTANCE_METRIC": self.distance_metric}
                ),
        )
        definition = IndexDefinition(prefix=self.get_prefix(), index_type=IndexType.HASH)
        self.connection.ft(self.name).create_index(fields=schema, definition=definition)

    def delete_collection(self):
        keys_to_delete = self.search_by_path( "*" )
        if len(keys_to_delete) > 0:
            for key in keys_to_delete:
                self.connection.delete(key)
        self.connection.execute_command('FT.DROPINDEX', self.name)
        return f"Collection {self.name} deleted"

    def list_documents(self):
        keys = [key for key in self.connection.scan_iter(f"{self.name}*")]
        # Check if the list is empty
        if len(keys) < 1:
            return []
        document_keys = [key.decode('utf-8').split(":")[1] for key in keys]
        unique_document_keys = list(set(document_keys))
        
        return unique_document_keys

    def add_documents(self, documents: List[schemas.Document]):
        existing_docs = self.list_documents()
        documents = [document_class.DocumentDB(jdoc=doc) for doc in documents if doc.path not in existing_docs]
        if len(documents) < 1:
            return 'Documents already exist'
        
        pipe = self.connection.pipeline()
        for documentDB in documents:
            blocks = documentDB.extract_info_blocks()
            for i,block in enumerate(blocks):
                key = self.get_key(documentDB.path, i)
                document_metadata = block.get_block_dict( self.VECTOR_FIELD_NAME )
                pipe.hset(key, mapping = document_metadata)
        pipe.execute()

        return 'Documents added'

    def update_document( self, path, document_update):
        notification = self.delete_document(path)
        if notification == "Document not found":
            return notification

        # convert basemodel class to DocumentDB
        documentDB = document_class.DocumentDB(path = path, jdoc = document_update)
        blocks = documentDB.extract_info_blocks()
        pipe = self.connection.pipeline()
        for i,block in enumerate(blocks):
            key = self.get_key(documentDB.path, i)
            document_metadata = block.get_block_dict(self.VECTOR_FIELD_NAME )
            pipe.hset(key, mapping = document_metadata)
        pipe.execute()

        return "Document updated"

    def delete_document(self, path):
        keys_to_delete = self.search_by_path(path)
        if len(keys_to_delete) < 1:
            return "Document not found"
        for key in keys_to_delete:
            self.connection.delete(key)

        return f"Document {path} deleted"

    def read_document(self, path):
        search_list = self.search_by_path( path)
        if len(search_list) > 0:
            return  [self.connection.hgetall( search_result )[b'text'] for search_result in search_list ]
        
        return "Document not found"
    
    def search_query(self, raw_query, top_k):
        print( f"Run search on: {raw_query}")
        query_vector_embed = llm.get_embedding(raw_query)
        base_query = f'*=>[KNN {top_k*2} @{self.VECTOR_FIELD_NAME} $vector]=>{{$yield_distance_as: dist}}'
        query = Query(base_query).sort_by('dist').return_fields("id", "dist").paging(0, top_k*2).dialect(2)    
        try:
            results = self.connection.ft(self.name).search(query, 
                                                           query_params={"vector": query_vector_embed.tobytes()}).docs
        except Exception as e:
            print("Error calling Redis search: ", e)
            return None
        
        result_dics = [ self.connection.hgetall( result['id'] ) for result in results ]
        scores = [ self.connection.hgetall( result['dist'] ) for result in results ]

        result_dics = [{key.decode('utf-8'): dict[key].decode('utf-8') for key \
                        in [b'render_id',b'path',b'title',b'content',b'text'] \
                            if key in dict} for dict in result_dics]
        result_dics = [dict for dict in result_dics if dict.get("content") == "1"]
        
        if len(result_dics) < 1 :
            return None

        return result_dics[:top_k], scores[:top_k]
    
    def QA_search(self, row_query, top_k = llm.TOP_LINKS):
        qnas = {}
        results = {}
        questions = llm.generate_questions(row_query, n = llm.N_QUESTIONS)
        print('Got questions!')
        for i, question in enumerate( questions ):
            search_results = self.search_query(raw_query = question, top_k = top_k )
            if search_results :
                result_dics, scores = search_results
            else:
                print( f"No result in question {i+1}")
                continue
            
            answer, referencies = llm.generate_answer(question, result_dics)
            
            for dict in result_dics:
                dict_id=f"{dict['path']}_{dict['render_id']}"
                results[dict_id] = schemas.SearchResult(id=dict_id, 
                                                    path = f"{dict['path']}#{dict['render_id']}",
                                                    title = dict['title']
                                                )
            
            qnas[str(i)] = schemas.QnA(question = question,answer = answer,links = " ".join(referencies))

        return schemas.SearchResultFull(qnas = qnas, results = results )

def list_collections() -> Any:
    return [x.decode('utf-8') for x in deps.db.connection.execute_command('FT._LIST')]

def get_collection(collection_name: str):
    return CollectionDB( collection_name)

CollectionDep = Annotated[CollectionDB, Depends(get_collection)]