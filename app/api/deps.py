from app.core.config import settings  # pylint: disable=C0415
from typing import Annotated, Optional
from fastapi import Depends, FastAPI

from redis import Redis
import cohere
from functools import cached_property
from app.schemas import collection

from typing import Optional
from fastapi import Depends

class Database:
    @cached_property
    def connection(self):
        # Initialize the connection to Redis
        # The parameters here are placeholders, replace with your actual parameters
        return Redis( host = settings.REDIS_HOST,
                    port = settings.REDIS_PORT,
                    password = settings.REDIS_PASSWORD)
    @cached_property
    def embedding(self):
        # Initialize the connection to Cohere
        return cohere.Client(settings.COHERE_API_KEY)
      
class CollectionDB():
    def __init__(self, connection: Redis, name: str):
        self.connection = connection
        self.name = name
    
    def get_a_prefix(self):
        return f"{self.name}"
    
    def get_a_key(self, document_key, block_num):
        return f"{self.get_a_prefix()}:{str(document_key)}:{str(block_num)}"
        
    def search_by_path(self, tag):
        # initialize a cursor
        cursor = 0
        # list to hold the results
        results = []
        # iterate over keys in the database that match the pattern
        while True:
            cursor, keys = self.connection.scan(cursor, match = self.get_a_key(tag, "*") )
            for key in keys:
                results.append(key)
            if cursor == 0:
                break
        return results

db = Database()

def get_collection(collection_name: str):
    return CollectionDB(db.connection, collection_name)

CollectionDep = Annotated[CollectionDB, Depends(get_collection)]