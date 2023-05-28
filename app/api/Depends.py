from app.core.config import settings  # pylint: disable=C0415

from redis import Redis
import cohere
from functools import cached_property

class Database:
    @cached_property
    def connection(self):
        # Initialize the connection to Redis
        # The parameters here are placeholders, replace with your actual parameters
        return Redis( host = settings.REDIS_HOST,
                    port = settings.REDIS_PORT,
                    password = settings.REDIS_PASSWORD)

class Collection:
    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
      
class Embedding:
    @cached_property
    def connection(self):
        # Initialize a Cohere client with your API key
        # This is a placeholder, replace with your actual Cohere client initialization
        return cohere.Client(settings.COHERE_API_KEY)

db = Database()
collection = Collection(db.connection, 'collection_name')

embedder = Embedding()