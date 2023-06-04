import lxml.html
import pandas as pd
import numpy as np
import string
import re
from redis.commands.search.query import Query

from app.api import deps, index
import openai


VECTOR_FIELD_NAME = 'encoded_text_block'
COHERE_MODEL = 'embed-multilingual-v2.0'
VECTOR_DIMENSIONS = 768
THRESHOLD = int(512/3 * 6 )

TOP_LINKS = 3
N_QUESTIONS = 3


# Load your OpenAI API key from an environment variable or secret management service
api_key = 

# Authenticate with the API
openai.api_key = api_key

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
def encode_blocks(cohere_client,text, cohere_model = COHERE_MODEL):
    """
    Function to encode blocks using Cohere
    """
    return np.array(cohere_client.embed(texts=[text],  model=cohere_model).embeddings[0]).astype(np.float32)

def generate_questions(prompt, model = "gpt-3.5-turbo", n = 5):
    message = {"role": "assistant", 
               "content": (f"""You are a search assistant. I enter a search query that could be misspelled.
                            Generate {n} questions in English I could ask using this words. Try to start 
                            with general questions and follow with more specific details about the object 
                            I'm asking about. Search query: {prompt}""")
                            }
    response = openai.ChatCompletion.create(model=model, messages=[message])
    questions = response['choices'][0]['message']['content'].split('\n')
    #print(f"First question is: {questions[0]} ")
    return questions

def generate_answer(question, search_results, redis_client, top_links):
    result_dicts = [ redis_client.hgetall( result['id'] ) for result in search_results ]
    result_df = pd.DataFrame.from_dict( result_dicts )[[b'render_id',b'path',b'content',b'text']]
    text_blocks_df =  result_df[result_df[b'content']==b'1']

    text_blocks = text_blocks_df[b'text'].iloc[0:top_links].apply(lambda x: x.decode('utf-8'))
    redis_path = text_blocks_df[b'path'].iloc[0:top_links].apply(lambda x: x.decode('utf-8'))
    redis_tag = text_blocks_df[b'render_id'].iloc[0:top_links].apply(lambda x: x.decode('utf-8'))
    blocks_with_refs = [f"------------------\n{j+1}. {redis_path.iloc[j]}_{redis_tag.iloc[j]}\n{block}\n" for j, block in enumerate(text_blocks)]
    concatenated_blocks = "\n".join(blocks_with_refs)
    message = { "role": "assistant",
                "content": (f"""You are an enterprise search assistant. Your task is to answer the question using the 
                            information that is provided in text blocks and provide references. There are lines of dashes separating 
                            text blocks. Each text block starts with an id and source URL and constitutes relevant information 
                            formatted as markdown. Formulate an answer using that information. After key sentences, put the reference 
                            numbers of the text block that supports the idea. When you finish with the answer, list all the sources 
                            used in order of relevance to the question. For references, use that format: reference number, id, url, 
                            and on the next line, a small citation from the text that highlights the document's importance. The 
                            question is:{question} \n {concatenated_blocks}""")
                }
    # Use OpenAI's gpt-4.0-turbo to generate a summary
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[message])
    answer = response['choices'][0]['message']['content']
    links = [f"[{j+1}] {path}_{redis_tag.iloc[j]}" for j, path in enumerate(redis_path)]

    return answer, links