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

import re
from collections import Counter

import time

import urllib.parse


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
        
    def search_by_doc_key(self, doc_key):
        cursor = 0
        results = []
        while True:
            cursor, keys = self.connection.scan(cursor, match = self.get_key(doc_key, "*") )
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
        schema = (  TagField("doc_id"),                     # Tag Field Name
                    VectorField(self.VECTOR_FIELD_NAME,     # Vector Field Name
                    "HNSW", 
                    {"TYPE": "FLOAT32", 
                    "DIM": self.VECTOR_DIMENSIONS, 
                    "DISTANCE_METRIC": self.distance_metric}
                ),
        )
        definition = IndexDefinition(prefix=[self.get_prefix()], index_type=IndexType.HASH)
        self.connection.ft(self.name).create_index(fields=schema, definition=definition)

    def delete_collection(self):
        keys_to_delete = self.search_by_doc_key( "*" )
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
        keys_decoded = [key.decode('utf-8').split(":") for key in keys]
        document_keys = [key[1] for key in keys_decoded]
        chunk_keys = [key[2] for key in keys_decoded]
        unique_document_keys = list(set(document_keys))
        chunk_keys_order = {key: i for i, key in enumerate(chunk_keys)}
        unique_document_keys.sort(key=lambda doc_key: chunk_keys_order.get(doc_key, float('inf')))
        
        return unique_document_keys

    def add_documents(self, documents: List[schemas.Document]):
        dalay = 10
        existing_docs = self.list_documents()
        documents = [document_class.DocumentDB(jdoc=doc) for doc in documents if doc.id not in existing_docs]
        if len(documents) < 1:
            return 'Documents already exist'
        
        failed_docs = []
        for i in range(0, len(documents), dalay):
            chunk_documents = documents[i:i+dalay]

            pipe = self.connection.pipeline()
            for documentDB in chunk_documents:
                try:
                    blocks = documentDB.extract_info_blocks_with_vectors()
                    for j, block in enumerate(blocks):
                        if block.content == 'True':
                            key = self.get_key(documentDB.doc_id, j)
                            document_metadata = block.get_block_dict(self.VECTOR_FIELD_NAME)
                            pipe.hset(key, mapping=document_metadata)
                except Exception as e:
                    print(f"Failed to add document with id {documentDB.doc_id}. Error: {e}")
                    failed_docs.append(documentDB.doc_id)
            pipe.execute()

        # If there are more documents to process, sleep for 60 seconds before the next request
        if i + dalay < len(documents):
            time.sleep(10)
        if len(failed_docs) > 0:
            return f'Failed to add documents with ids: {failed_docs}'
        else:
            return 'All documents added successfully'

    def update_document( self, doc_id, document_update):
        notification = self.delete_document(doc_id)
        if notification == "Document not found":
            return notification

        # convert basemodel class to DocumentDB
        documentDB = document_class.DocumentDB(id = doc_id, jdoc = document_update)
        blocks = documentDB.extract_info_blocks_with_vectors()
        pipe = self.connection.pipeline()
        for i,block in enumerate(blocks):
            key = self.get_key(documentDB.doc_id, i)
            document_metadata = block.get_block_dict(self.VECTOR_FIELD_NAME )
            pipe.hset(key, mapping = document_metadata)
        pipe.execute()

        return "Document updated"

    def delete_document(self, doc_id):
        keys_to_delete = self.search_by_doc_key(doc_id)
        if len(keys_to_delete) < 1:
            return "Document not found"
        for key in keys_to_delete:
            self.connection.delete(key)

        return f"Document {doc_id} deleted"

    def read_document(self, doc_id):
        search_list = self.search_by_doc_key( doc_id)
        if len(search_list) > 0:
            return  [self.connection.hgetall( search_result )[b'text'] for search_result in search_list ]
        
        return "Document not found"
    
    def search_query(self, query, top_k):
        query_vector_embed = np.array( llm.get_embedding([query])[0] ).astype(np.float32)
        base_query = f'*=>[KNN {top_k} @{self.VECTOR_FIELD_NAME} $vector]=>{{$yield_distance_as: dist}}'
        query = Query(base_query).sort_by('dist').return_fields("id", "dist").paging(0, top_k).dialect(2)    
        try:
            results = self.connection.ft(self.name).search(query, query_params={"vector": query_vector_embed.tobytes()}).docs
        except Exception as e:
            print("Error calling Redis search: ", e)
            return None
        result_dics = [ self.connection.hgetall( result['id'] ) for result in results ]
        result_dics = [{key.decode('utf-8'): dict[key].decode('utf-8') for key in [b'render_id',b'path',b'title',b'text',b'chunk_num'] if key in dict} for dict in result_dics]
        results = [ schemas.SearchResult(id=f"{dict['path']}#{dict['render_id']}#{dict['chunk_num']}", path = dict['path'], title = dict['title'], text = dict['text']) for dict in result_dics ]
        print(f'Got {len(results)} result on query')
        return results
    
    def QA_search(self, query, top_k = llm.TOP_LINKS_QnA ):
        questions = llm.generate_questions( query )
        qnas = []        
        results = []
        for i, question in enumerate( questions ):
            search_results = self.search_query( question, top_k )
            if search_results :
                results.extend(search_results)
                answer, references = llm.generate_answer(question, search_results)
                print(f'Got answer on :{question}')
                qnas.append(schemas.QnA(question = question, answer = answer, links=references ))
            else:
                print( f"No result in question {i+1}")
                continue
         # Filter out duplicates from all_results based on SearchResult.id
        seen_ids = set()
        unique_results = [result for result in results if not (result.id in seen_ids or seen_ids.add(result.id))]
        print(f'Got {len(unique_results)} unique references on questions')
        return qnas, unique_results
    
    def transform_search_results_to_documents(self, search_results ):
        documents_dict = {}
        for search_result in search_results:
            if search_result.path not in documents_dict:
                documents_dict[search_result.path] = schemas.SearchResultDocument(
                    title=search_result.title, path=search_result.path, text_blocks=[] )
            documents_dict[search_result.path].text_blocks.append(search_result.text)
        print( 'Change refs to docs' )
        return list(documents_dict.values())
    
    def full_search(self, query, top_k = llm.TOP_LINKS):
        initial_search_results = self.search_query(query, top_k )
        qnas, unique_results = self.QA_search( query )
        qnas_ranked, sorted_results = llm.change_ref_numbers( qnas, unique_results )

        return schemas.SearchResultFull(qnas = qnas_ranked, qnas_results = sorted_results, query_results = initial_search_results)

    def full_search_doc(self, query, top_k = llm.TOP_LINKS):
        initial_search_results = self.search_query(query, top_k )
        initial_search_docs = self.transform_search_results_to_documents(initial_search_results)
        qnas, unique_results = self.QA_search( query )
        unique_docs = self.transform_search_results_to_documents(unique_results)
        qnas_ranked, sorted_docs = llm.change_docs_numbers( qnas, unique_docs )

        return schemas.SearchResultFull(qnas = qnas_ranked, qnas_results = sorted_docs, query_results = initial_search_docs)

def list_collections() -> Any:
    return [x.decode('utf-8') for x in deps.db.connection.execute_command('FT._LIST')]

def get_collection(collection_name: str):
    return CollectionDB( collection_name)

CollectionDep = Annotated[CollectionDB, Depends(get_collection)]