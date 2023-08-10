import lxml.html
import re
from typing import List, Dict
import re
from copy import deepcopy

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



def get_embedding(texts, model=EMBEDDING_MODEL):
    return deps.db.embedding.embed(texts = texts,  model=model).embeddings

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
    refs = [f"[{j+1}] {path}_{tags[j]}" for j, path in enumerate(paths)]

    return answer, refs

def extract_info_blocks(db):
    parsed_html = lxml.html.fromstring(db.render)
    elements = parsed_html.xpath("//*")
    blocks = []
    current_block = {
        'render_id': 'undefined',
        'text': '',
        'chunk_num': 0,
        'content': 0,
        'path': db.path,
        'title': db.title,
        'locale': db.locale,
        'doc_id': db.doc_id
    }
    for element in elements:
        render_id = element.attrib.get('id', 'undefined')
        text_parts = [node.strip() for node in element.xpath("text()") if node.strip()]
        cleaned_text = " ".join(text_parts)
        cleaned_text = re.sub(r'[\n¶]', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        if cleaned_text:
            if render_id.startswith('p') or render_id == 'undefined':
                current_block['text'] += cleaned_text + '. '
                current_block['content'] = 1 if current_block['text'] else 0
            else:
                if current_block['text']:
                    if len(current_block['text']) > db.THRESHOLD :
                        texts = db.split_text(current_block['text'] )
                        for txt in texts:
                            current_block['text'] = txt
                            blocks.append(deepcopy(current_block))
                            current_block['chunk_num'] += 1
                    else:
                        blocks.append(deepcopy(current_block))
                current_block =  {
                    'render_id': render_id,
                    'text': cleaned_text + ' ', 
                    'chunk_num': 0,
                    'content': 0,
                    'path': db.path,
                    'title': db.title,
                    'locale': db.locale,
                    'doc_id': db.doc_id
                }
    if current_block['text']:
        if len(current_block['text']) > db.THRESHOLD :
            texts = db.split_text(current_block['text'] )
            for txt in texts:
                current_block['text'] = txt
                blocks.append(deepcopy(current_block))
                current_block['chunk_num'] += 1
        else:
            blocks.append(deepcopy(current_block))

    return blocks