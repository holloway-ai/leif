import lxml.html
import pandas as pd
import numpy as np
import string
import re
from redis.commands.search.query import Query
from typing import List, Optional, Dict

from app.api import deps
import openai
from app.core.config import settings  


TOP_LINKS = 3
N_QUESTIONS = 3

EMBEDDING_MODEL = 'embed-multilingual-v2.0'
VECTOR_DIMENSIONS = 768

# Load your OpenAI API key from an environment variable or secret management service
api_key = settings.OPENAI_API
openai.api_key = api_key

OPENAI_MODEL = "gpt-3.5-turbo"


def get_embedding(text, model=EMBEDDING_MODEL):
    vector = np.array( deps.db.embedding.embed(texts=[text],  model=model).embeddings[0] ).astype(np.float32)
    return vector

def generate_questions(prompt, model = OPENAI_MODEL, n = N_QUESTIONS):
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


def generate_answer(question, result_dics: List[Dict[str,str]]):
    paths = [ item['path'] for item in result_dics ]
    tags = [ item['render_id'] for item in result_dics ]
    texts = [ item['text'] for item in result_dics ]

    blocks_with_refs = [f"------------------\n{j+1}. {paths[j]}_{tags[j]}\n{text}\n" for j, text in enumerate(texts)]
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
    links = [f"[{j+1}] {path}_{tags[j]}" for j, path in enumerate(paths)]

    return answer, links