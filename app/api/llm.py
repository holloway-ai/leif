import lxml.html
import re
from typing import List, Dict
import re
from copy import deepcopy

from app.api import deps
import openai
from app.core.config import settings  
import re
from app import schemas

TOP_LINKS = 30
TOP_LINKS_QnA = 5

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
                            I'm asking about. Start each question from a new line. Do not answer questions! Search query: {prompt}""")
                            }
    response = openai.ChatCompletion.create(model=model, messages=[message])
    questions = response['choices'][0]['message']['content'].split('\n')
    return questions

def generate_questions_from_search(prompt, search_results, model = OPENAI_MODEL, n = N_QUESTIONS):
    doc_ids = [ item.id for item in search_results ]
    texts = [ item.text for item in search_results ]
    blocks_with_refs = [f"------------------\nDocument ({j+1}). {text}\n" for j, text in enumerate(texts)]
    refs = [f"[{j+1}] {doc_id}" for j, doc_id in enumerate(doc_ids)]
    concatenated_blocks = "\n".join(blocks_with_refs)
    message = {"role": "assistant", 
               "content": (f"""You are a search assistant. I enter a search query that could be misspelled,
                           and relevant documents found in my database after search.
                            Generate {n} questions in English I might ask using search query words and the
                            documents. Start each question with a new line. Do not answer questions! 
                            Search query: {prompt}. "------------------\nDocuments: 
                            {concatenated_blocks}""")
                            }
    response = openai.ChatCompletion.create(model=model, messages=[message])
    print(response['choices'][0]['message']['content'])
    questions = response['choices'][0]['message']['content'].split('\n')

    return questions, refs

def generate_answer(question, search_results):
    doc_ids = [ item.id for item in search_results ]
    texts = [ item.text for item in search_results ]
    blocks_with_refs = [f"------------------\nText block ({j+1}). {text}\n" for j, text in enumerate(texts)]
    refs = [f"[{j+1}] {doc_id}" for j, doc_id in enumerate(doc_ids)]
    concatenated_blocks = "\n".join(blocks_with_refs)
    message = { "role": "assistant",
                "content": (f"""You are an enterprise search assistant. Your task is to answer the question 
                            using the information provided in enumerated text blocks. There are lines of 
                            dashes separating text blocks. Formulate an answer using information, provided 
                            in the texts. After key sentences, put the reference number of the text block 
                            that supports the idea, in square brackets (For example, [1] or [2]). If 
                            provided information is not enough to answer the question, inform the user, do 
                            not speculate. The question is:{question} \n Text blocks: {concatenated_blocks}""")
                }
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[message])
    answer = response['choices'][0]['message']['content']

    return answer, doc_ids

def count_refs_in_answers( qnas ):
    result_counts_dict = {}
    for qna in qnas:
        references = qna.links #.split(' ')
        ref_list = [int(match) for match in re.findall(r'\[(\d+)\]', qna.answer)] 
        # Initialize SearchResult.id occurrences to 0 for this question
        for ref in references:
            if ref not in result_counts_dict:
                result_counts_dict[ref] = 0
        # Count occurrences of each SearchResult.id based on the answer
        for ref_num in ref_list:
            if 0 <= ref_num - 1 < len(references):
                ref_id = references[ref_num - 1]  
                result_counts_dict[ref_id] += 1

    return result_counts_dict

def count_docs_in_answers( qnas ):
    docs_counts_dict = {}
    for qna in qnas:
        references = qna.links #.split(' ')
        unique_docs = set([ref.split('#')[0] for ref in references])
        # Initialize SearchResult.id occurrences to 0 for this question
        for doc in unique_docs:
            if doc not in docs_counts_dict:
                docs_counts_dict[doc] = 0
        ref_list = [int(match) for match in re.findall(r'\[(\d+)\]', qna.answer)]
        # Count occurrences of each document (path) int the answer
        for ref_num in ref_list:            
            if 0 <= ref_num - 1 < len(references):
                ref_id = references[ref_num -1 ]  
                doc = ref_id.split('#')[0]  # Extract the path from the id
                docs_counts_dict[doc] += 1

    return docs_counts_dict

def change_ref_in_answer( qna, id_to_new_position ):
    new_answer = qna.answer
    references = qna.links #.split(' ')
    for old_id, new_position in id_to_new_position.items():
        if old_id in qna.links:
            old_position = references.index(old_id) + 1  # get the old position by finding the index in references
            new_answer = new_answer.replace(f"[{old_position}]", f"[{new_position}]")
        else:
            continue
    
    return new_answer

def change_docs_in_answer( qna, id_to_new_position ):
    new_answer = qna.answer
    ref_docs = [ref.split('#')[0] for ref in qna.links]
        
    # Create a mapping from old_position to new_position
    old_to_new_positions = {}
    for old_id, new_position in id_to_new_position.items():
        if old_id in ref_docs:
            old_positions = [idx + 1 for idx, ref in enumerate(ref_docs) if ref == old_id]
            for old_position in old_positions:
                old_to_new_positions[old_position] = new_position

    # Replace all old references with new doc id in the answer
    for old_position, new_position in old_to_new_positions.items():
        new_answer = re.sub(rf"\[{old_position}\]", f"[{new_position}]", new_answer)
            
    return new_answer

def change_ref_numbers( qnas, unique_results ):
    result_counts_dict = count_refs_in_answers( qnas )
    qnas_ranked = qnas
    sorted_results = sorted(unique_results, key=lambda r: result_counts_dict.get(r.id, 0), reverse=True)
    id_to_new_position = {result.id: idx+1 for idx, result in enumerate(sorted_results)}
    
    for qna in qnas_ranked:
        qna.answer = change_ref_in_answer( qna, id_to_new_position )

    return qnas_ranked, sorted_results

def change_docs_numbers( qnas, unique_docs ):
    docs_counts_dict = count_docs_in_answers( qnas )
    qnas_ranked = qnas
    sorted_docs = sorted(unique_docs, key=lambda r: docs_counts_dict.get(r.path, 0), reverse=True)
    id_to_new_position = {result.path: idx+1 for idx, result in enumerate(sorted_docs)}
    
    for qna in qnas_ranked:
        qna.answer = change_docs_in_answer( qna, id_to_new_position)
       
    return qnas_ranked, sorted_docs



def extract_info_blocks(db):
    parsed_html = lxml.html.fromstring(db.render)
    elements = parsed_html.xpath("//*")
    blocks = []
    current_block = {
        'render_id': 'undefined',
        'text': '',
        'chunk_num': 0,
        'content': 'False',
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
                # Add the conditional check here
                if cleaned_text.endswith(' .'):
                    current_block['text'] += ' '
                else:
                    current_block['text'] += cleaned_text + '. '
                current_block['content'] = 'True' if current_block['text'] else 'False'
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
                # Add the conditional check here
                if cleaned_text.endswith(' .'):
                    spacer = ' '
                else:
                    spacer = '. '
                current_block =  {
                    'render_id': render_id,
                    'text': cleaned_text + spacer, 
                    'chunk_num': 0,
                    'content': 'False',
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