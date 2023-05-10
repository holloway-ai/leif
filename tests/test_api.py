# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from app.main import app

from starlette.testclient import TestClient
import json
from typing import List

from app.api.api_v1.api import collection, document, search
from app.schemas import Collection, CollectionCreate, Document, DocumentUpdate, SearchResultFull, SearchResult

client = TestClient(app)

def test_docs_redirect():
    response = client.get("/")
    assert response.history[0].status_code in [302, 307]
    assert response.status_code == 200
    assert response.url == "http://testserver/docs"

# Test collection endpoints
def test_create_collection():
    new_collection = CollectionCreate(name="test_collection", description="test collection description")
    response = client.post("api/v1/collections/", json=new_collection.dict())
    assert response.status_code == 200

def test_get_collection():
    update_collection = CollectionCreate(name="test_collection", description="UPDATE test collection description")
    response = client.put("api/v1/collections/test_collection/", json=update_collection.dict())
    assert response.status_code == 200

def test_list_collections():
    response = client.get("api/v1/collections/")
    assert response.status_code == 200

# Test document endpoints
def test_add_documents():
    documents = [
        Document(path="test_document_1", localeCode="en", title="Test Document 1", description="Test Document 1",
                 render="test document 1 render").dict(),
        Document(path="test_document_2", localeCode="en", title="Test Document 2", description="Test Document 2",
                 render="test document 2 render").dict()
    ]
    response = client.post("api/v1/documents/test_collection/", json = documents)
    assert response.status_code == 200

def test_update_document():
    new_document = DocumentUpdate(localeCode="en", title="Updated Document", description="Updated Document",
                                  render="updated document render")
    response = client.put("api/v1/documents/test_collection/test_document_1", json=new_document.dict())
    assert response.status_code == 200

def test_list_documents():
    response = client.get("api/v1/documents/test_collection/")
    assert response.status_code == 200

def test_read_document():
    response = client.get("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

def test_delete_document():
    response = client.delete("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

# Test search endpoint
def test_search():
    response = client.get("api/v1/search/?query=Test Document 1")
    response_data = json.loads(response.content)
    assert response.status_code == 200
    assert isinstance(response_data, dict)
    assert "results" in response_data
    assert "suggestions" in response_data
    assert "totalHits" in response_data

# DELETE collection
def test_delete_collection():
    response = client.delete("api/v1/collections/test_collection/")
    assert response.status_code == 200

# Run all tests
def run_tests():
    test_docs_redirect()
    test_create_collection()
    test_get_collection()
    test_list_collections()
    test_add_documents()
    test_update_document()
    test_list_documents()
    test_read_document()
    test_delete_document()
    test_search()
    test_delete_collection()
    print("All tests passed!")