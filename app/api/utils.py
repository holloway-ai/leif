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

def get_a_prefix(collection_name):
    return f"{collection_name}"

def get_a_key(prefix, document_key, block_num):
    return f"{prefix}:{str(document_key)}:{str(block_num)}"

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

def extract_info_blocks(document, threshold=1200):
    parsed_html = lxml.html.fromstring(document)
    elements = parsed_html.xpath("//*")
    result = []
    current_block = {'tag_id': 'undefined', 'text': '', 'chunk_num': 0}

    for element in elements:
        tag_id = element.attrib.get('id', 'undefined')
        text_parts = [node.strip() for node in element.xpath("text()") if node.strip()]
        cleaned_text = " ".join(text_parts)
        cleaned_text = re.sub(r'[\n¶]', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        if cleaned_text:
            if tag_id.startswith('p') or tag_id == 'undefined':
                current_block['text'] += ' ' + cleaned_text
            else:
                if current_block['text']:
                    # split the current text block into chunks if it's too large
                    if len(current_block['text']) > threshold:
                        texts = split_text(current_block['text'], threshold)
                        for txt in texts:
                            current_block['text'] = txt
                            result.append(current_block.copy())
                            current_block['chunk_num'] += 1
                    else:
                        result.append(current_block.copy())
                current_block = {'tag_id': tag_id, 'text': cleaned_text + ' ', 'chunk_num': 0}

    # don't forget to add the last block
    if current_block['text']:
        if len(current_block['text']) > threshold:
            texts = split_text(current_block['text'], threshold)
            for txt in texts:
                current_block['text'] = txt
                result.append(current_block.copy())
                current_block['chunk_num'] += 1
        else:
            result.append(current_block.copy())

    return result

# Function to encode blocks using Cohere
def encode_blocks(cohere_conn,text, cohere_model = COHERE_MODEL):
    """
    Function to encode blocks using Cohere
    """
    return np.array(cohere_conn.embed(texts=[text],  model=cohere_model).embeddings[0]).astype(np.float32)


def search_by_path(redis_connect, collection_name, tag):
    # initialize a cursor
    cursor = 0
    # list to hold the results
    results = []
    # iterate over keys in the database that match the pattern
    while True:
        cursor, keys = redis_connect.scan(cursor, match = get_a_key(get_a_prefix(collection_name), tag, "*") )
        for key in keys:
            # retrieve the value for each key and append to results
            results.append(key)
        if cursor == 0:
            break

    return results

