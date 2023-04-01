from typing import Optional

from pydantic import BaseModel


# Shared properties
class CollectionBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on Collection creation
class CollectionCreate(CollectionBase):
    name: str


# Properties to receive on Collection update
class CollectionUpdate(CollectionBase):
    pass

# Properties shared by models stored in DB
class CollectionInDBBase(CollectionBase):
    pass

# Properties to return to client
class Collection(CollectionInDBBase):
    pass
