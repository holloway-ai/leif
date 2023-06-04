# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from app.main import app
import json

from starlette.testclient import TestClient
import json
from typing import List

from app.api.api_v1.api import collection, document, search
from app.schemas import Collection, Document
from app.api import utils

client = TestClient(app)

with open('json') as file:
    test_docs = json.load(file)

test_doc = test_docs[0]
test_doc_update = test_docs[1]

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

def test_update_document():
    # Check if the "test_collection" exists and create it if not
    new_collection = CollectionCreate(name="test_collection", description="Test collection")
    client.post("api/v1/collections/", json=new_collection.dict())
    new_documents = [test_doc]
    response = client.post("api/v1/documents/test_collection/", json = new_documents)

    response = client.put("api/v1/documents/test_collection/test_document_1", json=test_doc_update)
    assert response.status_code == 200

def test_read_document():
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    # Parse the JSON response data
    existing_collections = existing_collections.json()
    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

        documents = [Document(path="test_document_1", localeCode="en", title="Test Document 1", 
                              description="Test Document 1", render="test document 1 render").dict()]
        response = client.post("api/v1/documents/test_collection/", json = documents)

    response = client.get("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

def test_delete_document():
    # Check if the "test_collection" exists and create it if not
    existing_collections = client.get("api/v1/collections/")
    existing_collections = existing_collections.json()

    if "test_collection" not in existing_collections:
        new_collection = Collection(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())
        documents = [Document(path="test_document_1", localeCode="en", title="Test Document 1", 
                              description="Test Document 1", render="test document 1 render").dict()]
        response = client.post("api/v1/documents/test_collection/", json = documents)

    response = client.delete("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

# Test search endpoint
def test_search():
    response = client.get("api/v1/search/?query=Questions about God")
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

# Test collection endpoints
def test_create_collection():
    new_collection = Collection(name="test_collection", description="test collection description")
    response = client.post("api/v1/collections/", json=new_collection.dict())
    assert response.status_code == 200

# Test document endpoints
def test_add_documents():
    new_documents = [ test_doc ]
    response = client.post("api/v1/documents/test_collection/", json = new_documents)
    assert response.status_code == 200

def test_lxml():
    html_text = """<head></head>
    <body><div>
    <h2>Header </h2> <p> simple text </p>
    <p><span>span text</span><span> span 2</span></p>
    </div></body>
    """
    assert utils.extract_info_blocks(html_text)[0]['text'] == ' Header simple text span text span 2'


def test_lxml_with_multiple_divs():
    html_text = """<head></head>
    <body><div><h2>Header </h2></div><div><p> simple text </p></div><div><p><span>span text</span><span> span 2</span></p></div></body>
    """
    assert utils.extract_info_blocks(html_text)[0]['text'] == ' Header simple text span text span 2'


def test_lxml_with_nested_divs():
    html_text = """<head></head>
    <body><div><div><h2>Header </h2></div><div><p> simple text </p></div><div><p><span>span text</span><span> span 2</span></p></div></div></body>
    """
    assert utils.extract_info_blocks(html_text)[0]['text'] == ' Header simple text span text span 2'


def test_lxml_with_lists():
    html_text = """<head></head>
    <body><div><h2>Header </h2><ul><li>list item 1</li><li>list item 2</li></ul><p> simple text </p><p><span>span text</span><span> span 2</span></p></div></body>
    """
    assert utils.extract_info_blocks(html_text)[0]['text'] == ' Header list item 1 list item 2 simple text span text span 2'


def test_lxml_with_tables():
    html_text = """<head></head>
    <body><div><h2>Header </h2><table><tr><td>table cell 1</td><td>table cell 2</td></tr></table><p> simple text </p><p><span>span text</span><span> span 2</span></p></div></body>
    """
    assert utils.extract_info_blocks(html_text)[0]['text'] == ' Header table cell 1 table cell 2 simple text span text span 2'