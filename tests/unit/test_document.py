

from app.main import app

from starlette.testclient import TestClient
import json
import pytest

from app.api import llm

from app.api.classes import document as document_class
from app.schemas import Document

client = TestClient(app)

def test_lxml():
    html_text = """<head></head>
    <body><div>
    <h2>Header </h2> <p> simple text </p>
    <p><span>span text</span><span> span 2</span></p>
    </div></body>
    """

    document = Document(
        id="dummy_doc_id",
        path="dummy_path",
        locale="dummy_locale",
        title="dummy_title",
        description="dummy_description",
        render=html_text,
    )

    document_db = document_class.DocumentDB(document)
    
    block_dicts = llm.extract_info_blocks(document_db)
    assert block_dicts[0]['text'] == 'Header. simple text. span text. span 2. '


def test_lxml_with_multiple_divs():
    html_text = """<head></head>
    <body><div><h2>Header </h2></div><div><p> simple text </p></div><div><p><span>span text</span><span> span 2</span></p></div></body>
    """
    document = Document(
        id="dummy_doc_id",
        path="dummy_path",
        locale="dummy_locale",
        title="dummy_title",
        description="dummy_description",
        render=html_text,
    )

    document_db = document_class.DocumentDB(document)
    
    block_dicts = llm.extract_info_blocks(document_db)
    assert block_dicts[0]['text'] == 'Header. simple text. span text. span 2. '


def test_lxml_with_nested_divs():
    html_text = """<head></head>
    <body><div><div><h2>Header </h2></div><div><p> simple text </p></div><div><p><span>span text</span><span> span 2</span></p></div></div></body>
    """
    document = Document(
        id="dummy_doc_id",
        path="dummy_path",
        locale="dummy_locale",
        title="dummy_title",
        description="dummy_description",
        render=html_text,
    )

    document_db = document_class.DocumentDB(document)
    
    block_dicts = llm.extract_info_blocks(document_db)

    assert block_dicts[0]['text'] == 'Header. simple text. span text. span 2. '


def test_lxml_with_lists():
    html_text = """<head></head>
    <body><div><h2>Header </h2><ul><li>list item 1</li><li>list item 2</li></ul><p> simple text </p><p><span>span text</span><span> span 2</span></p></div></body>
    """
    document = Document(
        id="dummy_doc_id",
        path="dummy_path",
        locale="dummy_locale",
        title="dummy_title",
        description="dummy_description",
        render=html_text,
    )

    document_db = document_class.DocumentDB(document)
    
    block_dicts = llm.extract_info_blocks(document_db)

    assert block_dicts[0]['text'] == 'Header. list item 1. list item 2. simple text. span text. span 2. '


def test_lxml_with_tables():
    html_text = """<head></head>
    <body><div><h2>Header </h2><table><tr><td>table cell 1</td><td>table cell 2</td></tr></table><p> simple text </p><p><span>span text</span><span> span 2</span></p></div></body>
    """
    document = Document(
        id="dummy_doc_id",
        path="dummy_path",
        locale="dummy_locale",
        title="dummy_title",
        description="dummy_description",
        render=html_text,
    )

    document_db = document_class.DocumentDB(document)
    
    block_dicts = llm.extract_info_blocks(document_db)

    assert block_dicts[0]['text'] == 'Header. table cell 1. table cell 2. simple text. span text. span 2. '