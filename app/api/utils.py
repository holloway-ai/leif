import lxml.html
import cohere
import numpy as np
import string
import re

from fastapi import APIRouter, HTTPException
from redis import Redis
from app.shared_state import existing_collections

VECTOR_FIELD_NAME = 'encoded_text_block'
COHERE_MODEL = 'embed-multilingual-v2.0'
VECTOR_DIMENSIONS = 768
THRESHOLD = int(512/3 * 6 )
INDEX_NAME = "index_HNSW"                         # Vector Index Name
DOC_PREFIX = "doc_block:"                         # RediSearch Key Prefix for the Index

def get_a_key(prefix, collection_key, document_key, block_num):
    return f"{prefix}:{collection_key}:{document_key}:{str(block_num)}"

def split_text(text, threshold):
    # split the text into sentences
    sentences = re.split('(?<=[.!?])\s', text)
    blocks = []
    current_block = ''

    for sentence in sentences:
        if len(current_block + sentence) <= threshold:
            current_block += sentence
        else:
            blocks.append(current_block)
            current_block = sentence

    blocks.append(current_block)
    return blocks


def extract_info_blocks(document, threshold):
    parsed_html = lxml.html.fromstring(document)
    elements = parsed_html.xpath("//*[@id or self::p]")

    info_blocks = []
    current_block = {'tag_id': None, 'text': '', 'chunk_num': 0}

    for element in elements:
        text = element.text_content().strip() if element.text_content() else ''
        tag_id = element.attrib.get('id', 'undefined')

        # Clean text - remove "\n", "¶" and other special characters
        cleaned_text = re.sub(r'[\n¶]', ' ', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        if tag_id.startswith('p') or tag_id == 'undefined':
            if cleaned_text:
                current_block['text'] += ' ' + cleaned_text
        else:
            if current_block['tag_id']:
                # split the current text block into chunks if it's too large
                if len(current_block['text']) > threshold:
                    texts = split_text(current_block['text'], threshold)
                    for txt in texts:
                        if len(txt.split()) >= 3:  # only add the block if the text has at least 3 words
                            info_blocks.append({
                                'tag_id': current_block['tag_id'], 
                                'text': txt, 
                                'chunk_num': current_block['chunk_num']
                            })
                            current_block['chunk_num'] += 1
                elif len(current_block['text'].split()) >= 3:  # only add the block if the text has at least 3 words
                    info_blocks.append(current_block)

            current_block = {'tag_id': tag_id, 'text': cleaned_text + ' ', 'chunk_num': 0}

    # don't forget to add the last block
    if current_block['tag_id']:
        if len(current_block['text']) > threshold:
            texts = split_text(current_block['text'], threshold)
            for txt in texts:
                if len(txt.split()) >= 3:  # only add the block if the text has at least 3 words
                    info_blocks.append({
                        'tag_id': current_block['tag_id'], 
                        'text': txt, 
                        'chunk_num': current_block['chunk_num']
                    })
                    current_block['chunk_num'] += 1
        elif len(current_block['text'].split()) >= 3:  # only add the block if the text has at least 3 words
            info_blocks.append(current_block)

    return info_blocks

# Function to encode blocks using Cohere
def encode_blocks(cohere_conn,text, cohere_model = COHERE_MODEL):
    """
    Function to encode blocks using Cohere
    """
    return np.array(cohere_conn.embed(texts=[text],  model=cohere_model).embeddings[0]).astype(np.float32)

def get_collection_by_name(name: str):
    """
    Return collection by name
    """
    collection = existing_collections.get(name)
    if collection:
        return collection
    raise HTTPException(status_code=404, detail="Collection not found")

def search_by_path(redis_connect, collection_name, tag):
    # initialize a cursor
    cursor = 0
    # list to hold the results
    results = []
    # iterate over keys in the database that match the pattern
    while True:
        cursor, keys = redis_connect.scan(cursor, match = get_a_key(DOC_PREFIX, collection_name, tag, "*"))
        for key in keys:
            # retrieve the value for each key and append to results
            results.append(key)
        if cursor == 0:
            break

    return results

