# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from app.main import app

from starlette.testclient import TestClient
import pytest

from typing import List

from app.api.api_v1.api import collection, document, search
from app.schemas import Collection, Document
from app.api import llm
import json

client = TestClient(app)

# This is your fixture function
@pytest.fixture(scope="session")
def test_docs():
    json_file_path = os.path.join(os.path.dirname(__file__), 'test_documents.json')
    with open(json_file_path) as json_file:
        data = json.load(json_file)
    return data

@pytest.fixture
def test_doc(test_docs):
    return test_docs[0]

@pytest.fixture
def test_doc_update(test_docs):
    return test_docs[1]

def test_docs_redirect():
    response = client.get("/")
    assert response.history[0].status_code in [302, 307]
    assert response.status_code == 200
    assert response.url == "http://testserver/docs"

def test_list_collections():
    # Check if the "test_collection" exists and create it if not
    response = client.get("api/v1/collections/")
    assert response.status_code == 200

def test_list_documents():
    response = client.get("api/v1/documents/test_collection/")
    assert response.status_code == 200

def test_update_document(test_doc, test_doc_update):
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    # Parse the JSON response data
    existing_collections = existing_collections.json()
    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())
    
    new_documents = [test_doc]  # test_doc is already a dictionary
    response = client.post("api/v1/documents/test_collection/", json=new_documents)

    response = client.put("api/v1/documents/test_collection/test_document_1", json=test_doc_update)
    assert response.status_code == 200

def test_read_document(test_doc):
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    # Parse the JSON response data
    existing_collections = existing_collections.json()
    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    new_documents = [ test_doc ]
    response = client.post("api/v1/documents/test_collection/", json = new_documents)

    response = client.get("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

def test_delete_document():
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    existing_collections = existing_collections.json()

    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())
        new_documents = [ test_doc ]
        response = client.post("api/v1/documents/test_collection/", json = new_documents)

    response = client.delete("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

# DELETE collection
def test_delete_collection():
       # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    existing_collections = existing_collections.json()
    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())
    response = client.delete("api/v1/collections/test_collection/")
    assert response.status_code == 200

# Test collection endpoints
def test_create_collection():
    new_collection = Collection(name="test_collection", description="test collection description")
    response = client.post("api/v1/collections/", json=new_collection.dict())
    assert response.status_code == 200

# Test document endpoints
def test_add_documents(test_doc, test_doc_update):
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    # Parse the JSON response data
    existing_collections = existing_collections.json()
    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())
    new_documents = [ test_doc ]
    response = client.post("api/v1/documents/test_collection/", json = new_documents)
    assert response.status_code == 200


# Test search endpoint
def test_search():
    response = client.get("api/v1/search/test_collection/?query=Questions about God")
    response_data = json.loads(response.content)
    assert response.status_code == 200
