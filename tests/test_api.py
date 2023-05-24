# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from app.main import app

from starlette.testclient import TestClient
import json
from typing import List

from app.api.api_v1.api import collection, document, search
from app.schemas import Collection, CollectionCreate, Document, DocumentUpdate, SearchResultFull, SearchResult
from app.shared_state import existing_collections

client = TestClient(app)

test_doc = {
    "path": "test_document_1",
    "localeCode": "en",
    "title": "I am the test Doc 1",
    "description": "bla bla bla",
    "render": "<h1 class=\"toc-header\" id=\"holloway-whitepaper\"><a href=\"#holloway-whitepaper\" class=\"toc-anchor\">¶</a> Holloway Whitepaper</h1>\n<p class=\"content\" id=\"p0\">Holloway is a next-generation corporate knowledge management tool that offers semantic search capabilities using open-source technology, making knowledge accessible and easy to find.</p>\n<h3 class=\"toc-header\" id=\"contents\"><a href=\"#contents\" class=\"toc-anchor\">¶</a> Contents</h3>\n<br><div> \n</div><h6 class=\"toc-header\" id=\"i-introduction\"><a href=\"#i-introduction\" class=\"toc-anchor\">¶</a> I. Introduction</h6>\n<blockquote class=\"is-info content\" id=\"p1\">\n<p>1.1. Explanation of the problem with current knowledge management systems<br>\n1.2. Description of Holloway's solution<br>\n1.3. Overview of the whitepaper</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"ii-the-problem-with-current-knowledge-management-systems\"><a href=\"#ii-the-problem-with-current-knowledge-management-systems\" class=\"toc-anchor\">¶</a> II. The Problem with Current Knowledge Management Systems</h6>\n<blockquote class=\"is-info content\" id=\"p2\">\n<p>2.1. Description of current knowledge management systems limitations<br>\n2.2. Explanation of the importance of effective knowledge management<br>\n2.3. Discussion of the challenges faced by fast-growing companies</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"iii-the-solution-holloway\"><a href=\"#iii-the-solution-holloway\" class=\"toc-anchor\">¶</a> III. The Solution: Holloway</h6>\n<blockquote class=\"is-info content\" id=\"p3\">\n<p>3.1. Overview of Holloway's search capabilities<br>\n3.2. Explanation of how Holloway's technology differs from existing solutions<br>\n3.3. Description of Cohere's LLM-powered Multilingual Text Understanding model and Qdrant's vector search engine<br>\n3.4. Discussion of the benefits of using open-source solutions</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"iv-implementation\"><a href=\"#iv-implementation\" class=\"toc-anchor\">¶</a> IV. Implementation</h6>\n<blockquote class=\"is-info content\" id=\"p4\">\n<p>4.1. Discussion of the process of implementing Holloway<br>\n4.2. Explanation of the decision to use wiki.js as a base<br>\n4.3. Description of the benefits of using external search engines<br>\n4.4. Discussion of the technical challenges of implementing the search engine</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"v-uploading-and-indexing-videos\"><a href=\"#v-uploading-and-indexing-videos\" class=\"toc-anchor\">¶</a> V. Uploading and Indexing Videos</h6>\n<blockquote class=\"is-info content\" id=\"p5\">\n<p>5.1. Explanation of the importance of video content<br>\n5.2. Discussion of the technical difficulties in managing video content<br>\n5.3. Description of Holloway's solution to these difficulties<br>\n5.4. Explanation of the benefits of semantic search for video content</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"vi-conclusion\"><a href=\"#vi-conclusion\" class=\"toc-anchor\">¶</a> VI. Conclusion</h6>\n<blockquote class=\"is-info content\" id=\"p6\">\n<p>6.1. Recap of the problem with current knowledge management systems<br>\n6.2. Summary of Holloway's solution<br>\n6.3. Discussion of the potential impact of Holloway on corporate knowledge management<br>\n6.4. Call to action for companies to adopt Holloway.</p>\n</blockquote>\n<hr>\n<br>\n<h3 class=\"toc-header\" id=\"i-introduction-1\"><a href=\"#i-introduction-1\" class=\"toc-anchor\">¶</a> I. Introduction</h3>\n<h6 class=\"toc-header\" id=\"h-11-explanation-of-the-problem-with-current-knowledge-management-systems\"><a href=\"#h-11-explanation-of-the-problem-with-current-knowledge-management-systems\" class=\"toc-anchor\">¶</a> 1.1. Explanation of the problem with current knowledge management systems</h6>\n<p class=\"content\" id=\"p7\">Current knowledge management systems, such as Confluence by Atlassian, lack efficient search capabilities, which makes it difficult to access corporate knowledge. This issue becomes even more pronounced in fast-growing companies with changing structures and responsibilities.<br>\n<br></p>\n<h6 class=\"toc-header\" id=\"h-12-description-of-holloways-solution\"><a href=\"#h-12-description-of-holloways-solution\" class=\"toc-anchor\">¶</a> 1.2. Description of Holloway's solution</h6>\n<p class=\"content\" id=\"p8\">Holloway is a next-generation corporate knowledge management tool that offers semantic search capabilities using open-source technology. It addresses the limitations of existing systems by providing efficient and accurate search results, making knowledge more accessible to employees.<br>\n<br></p>\n<h6 class=\"toc-header\" id=\"h-13-overview-of-the-whitepaper\"><a href=\"#h-13-overview-of-the-whitepaper\" class=\"toc-anchor\">¶</a> 1.3. Overview of the whitepaper</h6>\n<p class=\"content\" id=\"p9\">This whitepaper will provide an in-depth analysis of the challenges posed by current knowledge management systems and how Holloway provides a solution to these challenges. It will explore the technology behind Holloway's semantic search capabilities and the benefits of using open-source solutions. The paper will also discuss future plans for video indexing and the potential impact of Holloway on corporate knowledge management.</p>\n<br>\n<h3 class=\"toc-header\" id=\"ii-the-problem-with-current-knowledge-management-systems-1\"><a href=\"#ii-the-problem-with-current-knowledge-management-systems-1\" class=\"toc-anchor\">¶</a> II. The Problem with Current Knowledge Management Systems</h3>\n<h6 class=\"toc-header\" id=\"h-21-description-of-current-knowledge-management-systems-limitations\"><a href=\"#h-21-description-of-current-knowledge-management-systems-limitations\" class=\"toc-anchor\">¶</a> 2.1. Description of current knowledge management systems limitations</h6>\n"
  }

test_doc_update = {
    "localeCode": "en",
    "title": "I am the UPDATED test Doc 1",
    "description": "bla bla bla UPDATED",
    "render": "<h1 class=\"toc-header\" id=\"holloway-whitepaper\"><a href=\"#holloway-whitepaper\" class=\"toc-anchor\">¶</a> Holloway Whitepaper</h1>\n<p class=\"content\" id=\"p0\">Holloway is a next-generation corporate knowledge management tool that offers semantic UPDATED search capabilities using open-source technology, making knowledge accessible UPDATED and easy to find.</p>\n<h3 class=\"toc-header\" id=\"contents\"><a href=\"#contents\" class=\"toc-anchor\">¶</a> Contents</h3>\n<br><div> \n</div><h6 class=\"toc-header\" id=\"i-introduction\"><a href=\"#i-introduction\" class=\"toc-anchor\">¶</a> I. Introduction UPDATED</h6>\n<blockquote class=\"is-info content\" id=\"p1\">\n<p>1.1. Explanation of the problem with current knowledge management UPDATED systems<br>\n1.2. Description of Holloway's solution<br>\n1.3. UPDATED Overview of the whitepaper</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"ii-the-problem-with-current-knowledge-management-systems\"><a href=\"#ii-the-problem-with-current-knowledge-management-systems\" class=\"toc-anchor\">¶</a> II. UPDATED The Problem with Current Knowledge Management Systems</h6>\n<blockquote class=\"is-info content\" id=\"p2\">\n<p>2.1. UPDATED Description of current knowledge management systems limitations<br>\n2.2. UPDATED Explanation of the importance of effective knowledge management<br>\n2.3. Discussion of the challenges faced by fast-growing companies</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"iii-the-solution-holloway\"><a href=\"#iii-the-solution-holloway\" class=\"toc-anchor\">¶</a> III. UPDATED The Solution: Holloway</h6>\n<blockquote class=\"is-info content\" id=\"p3\">\n<p>3.1. Overview of Holloway's search capabilities<br>\n3.2. Explanation of how Holloway's technology differs from existing solutions<br>\n3.3. Description of Cohere's LLM-powered Multilingual Text Understanding model and Qdrant's vector search engine<br>\n3.4. Discussion of the benefits of using open-source solutions</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"iv-implementation\"><a href=\"#iv-implementation\" class=\"toc-anchor\">¶</a> IV. Implementation</h6>\n<blockquote class=\"is-info content\" id=\"p4\">\n<p>4.1. Discussion of the process of implementing Holloway<br>\n4.2. Explanation of the decision to use wiki.js as a base<br>\n4.3. Description of the benefits of using external search engines<br>\n4.4. Discussion of the technical challenges of implementing the search engine</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"v-uploading-and-indexing-videos\"><a href=\"#v-uploading-and-indexing-videos\" class=\"toc-anchor\">¶</a> V. Uploading and Indexing Videos</h6>\n<blockquote class=\"is-info content\" id=\"p5\">\n<p>5.1. Explanation of the importance of video content<br>\n5.2. Discussion of the technical difficulties in managing video content<br>\n5.3. Description of Holloway's solution to these difficulties<br>\n5.4. Explanation of the benefits of semantic search for video content</p>\n</blockquote>\n<h6 class=\"toc-header\" id=\"vi-conclusion\"><a href=\"#vi-conclusion\" class=\"toc-anchor\">¶</a> VI. Conclusion</h6>\n<blockquote class=\"is-info content\" id=\"p6\">\n<p>6.1. Recap of the problem with current knowledge management systems<br>\n6.2. Summary of Holloway's solution<br>\n6.3. Discussion of the potential impact of Holloway on corporate knowledge management<br>\n6.4. Call to action for companies to adopt Holloway.</p>\n</blockquote>\n<hr>\n<br>\n<h3 class=\"toc-header\" id=\"i-introduction-1\"><a href=\"#i-introduction-1\" class=\"toc-anchor\">¶</a> I. Introduction</h3>\n<h6 class=\"toc-header\" id=\"h-11-explanation-of-the-problem-with-current-knowledge-management-systems\"><a href=\"#h-11-explanation-of-the-problem-with-current-knowledge-management-systems\" class=\"toc-anchor\">¶</a> 1.1. Explanation of the problem with current knowledge management systems</h6>\n<p class=\"content\" id=\"p7\">Current knowledge management systems, such as Confluence by Atlassian, lack efficient search capabilities, which makes it difficult to access corporate knowledge. This issue becomes even more pronounced in fast-growing companies with changing structures and responsibilities.<br>\n<br></p>\n<h6 class=\"toc-header\" id=\"h-12-description-of-holloways-solution\"><a href=\"#h-12-description-of-holloways-solution\" class=\"toc-anchor\">¶</a> 1.2. Description of Holloway's solution</h6>\n<p class=\"content\" id=\"p8\">Holloway is a next-generation corporate knowledge management tool that offers semantic search capabilities using open-source technology. It addresses the limitations of existing systems by providing efficient and accurate search results, making knowledge more accessible to employees.<br>\n<br></p>\n<h6 class=\"toc-header\" id=\"h-13-overview-of-the-whitepaper\"><a href=\"#h-13-overview-of-the-whitepaper\" class=\"toc-anchor\">¶</a> 1.3. Overview of the whitepaper</h6>\n<p class=\"content\" id=\"p9\">This whitepaper will provide an in-depth analysis of the challenges posed by current knowledge management systems and how Holloway provides a solution to these challenges. It will explore the technology behind Holloway's semantic search capabilities and the benefits of using open-source solutions. The paper will also discuss future plans for video indexing and the potential impact of Holloway on corporate knowledge management.</p>\n<br>\n<h3 class=\"toc-header\" id=\"ii-the-problem-with-current-knowledge-management-systems-1\"><a href=\"#ii-the-problem-with-current-knowledge-management-systems-1\" class=\"toc-anchor\">¶</a> II. The Problem with Current Knowledge Management Systems</h3>\n<h6 class=\"toc-header\" id=\"h-21-description-of-current-knowledge-management-systems-limitations\"><a href=\"#h-21-description-of-current-knowledge-management-systems-limitations\" class=\"toc-anchor\">¶</a> 2.1. Description of current knowledge management systems limitations</h6>\n"
  }

def test_docs_redirect():
    response = client.get("/")
    assert response.history[0].status_code in [302, 307]
    assert response.status_code == 200
    assert response.url == "http://testserver/docs"

def test_update_collection():
    # Check if the "test_collection" exists and create it if not
    if "test_collection" not in existing_collections:
        new_collection = CollectionCreate(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    update_collection = CollectionCreate(name="test_collection", description="UPDATE test collection description")
    response = client.put("api/v1/collections/test_collection/", json=update_collection.dict())
    assert response.status_code == 200

def test_list_collections():
    # Check if the "test_collection" exists and create it if not
    if "test_collection" not in existing_collections:
        new_collection = CollectionCreate(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    response = client.get("api/v1/collections/")
    assert response.status_code == 200

def test_list_documents():
    response = client.get("api/v1/documents/test_collection/")
    assert response.status_code == 200

def test_update_document():
    # Check if the "test_collection" exists and create it if not
    if "test_collection" not in existing_collections:
        new_collection = CollectionCreate(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    # Check if the document "test_document_1" exists and create it if not
    collection_for_test = document.utils.get_collection_by_name("test_collection")
    if "test_document_1" not in collection_for_test.documents:
        new_documents = [test_doc]
        response = client.post("api/v1/documents/test_collection/", json = new_documents)

    response = client.put("api/v1/documents/test_collection/test_document_1", json=test_doc_update)
    assert response.status_code == 200

def test_read_document():
    # Check if the "test_collection" exists and create it if not
    if "test_collection" not in existing_collections:
        new_collection = CollectionCreate(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    # Check if the document "test_document_1" exists and create it if not
    collection_for_test = document.utils.get_collection_by_name("test_collection")
    if "test_document_1" not in collection_for_test.documents:
        documents = [Document(path="test_document_1", localeCode="en", title="Test Document 1", 
                              description="Test Document 1", render="test document 1 render").dict()]
        response = client.post("api/v1/documents/test_collection/", json = documents)

    response = client.get("api/v1/documents/test_collection/test_document_1")
    assert response.status_code == 200

def test_delete_document():
    # Check if the "test_collection" exists and create it if not
    if "test_collection" not in existing_collections:
        new_collection = CollectionCreate(name="test_collection", description="Test collection")
        client.post("api/v1/collections/", json=new_collection.dict())

    # Check if the document "test_document_1" exists and create it if not
    collection_for_test = document.utils.get_collection_by_name("test_collection")
    if "test_document_1" not in collection_for_test.documents:
        documents = [Document(path="test_document_1", localeCode="en", title="Test Document 1", 
                              description="Test Document 1", render="test document 1 render").dict()]
        response = client.post("api/v1/documents/test_collection/", json = documents)

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

# Test collection endpoints
def test_create_collection():
    new_collection = CollectionCreate(name="test_collection", description="test collection description")
    response = client.post("api/v1/collections/", json=new_collection.dict())
    assert response.status_code == 200

# Test document endpoints
def test_add_documents():
    new_documents = [ test_doc ]
    response = client.post("api/v1/documents/test_collection/", json = new_documents)
    assert response.status_code == 200


# Run all tests
def run_tests():
    test_docs_redirect()
    test_update_collection()
    test_list_collections()
    test_update_document()
    test_list_documents()
    test_read_document()
    test_delete_document()
    test_search()
    test_delete_collection()
    test_create_collection()
    test_add_documents()
    print("All tests passed!")