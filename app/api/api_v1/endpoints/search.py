from typing import Any, List
from fastapi import APIRouter, HTTPException
from app import schemas
from app.api import utils
from app.api import index
from app.api import deps

from app.core.config import settings  # pylint: disable=C0415

router = APIRouter()

import lxml.html
import numpy as np


@router.get("/", response_model = schemas.SearchResultFull)
def search(query: str) -> Any:   
    # A dictionary to store top_k results for each question across all collections
    top_results = {}

    question_results = []
    results = []
    answers = []
    links = []
    # Generate questions from the query
    questions = utils.generate_questions(query, n = utils.N_QUESTIONS)
    existing_collections = [x.decode('utf-8') for x in deps.db.connection.execute_command('FT._LIST')]
    #print("Find Existing Collections!")
    if len(existing_collections) < 1:
        raise HTTPException(status_code=404, detail="No Collections")

    for question in questions:
        query_embedding = utils.encode_blocks(deps.db.embedding, question)
        # A list to store the search results for the current question from all collections
        for collection in existing_collections:
            #print(f"Search in {collection} ")
            redis_search_results = index.search_vectors_knn(redis_connect = deps.db.connection, 
                                                            query_vector = query_embedding, 
                                                            index_name = collection, 
                                                            vector_name = utils.VECTOR_FIELD_NAME, 
                                                            top_k = utils.TOP_LINKS)
            #print(f"print 1 hit: {redis_search_results}")
            if redis_search_results is not None:
                question_results.extend(redis_search_results)
                #print(f"Add result from {collection}")

        # Sort the search results for the current question based on the scores and select top_k results
        sorted_list = sorted(question_results, key=lambda x: float(x['dist']))
        top_results[question] = sorted_list[:utils.TOP_LINKS]
        #print(' Store best 5 for a question!')

        for redis_doc in top_results[question]:
            redis_dict = deps.db.connection.hgetall(redis_doc['id'].encode('utf-8'))
            #print(redis_doc['id'])

            redis_path = redis_dict['path'.encode('utf-8')].decode('utf-8')
            redis_tag = redis_dict['render_id'.encode('utf-8')].decode('utf-8')
            title = redis_dict['title'.encode('utf-8')] if 'title'.encode('utf-8') in redis_dict else None
            description = redis_dict['text'.encode('utf-8')] if 'text'.encode('utf-8') in redis_dict else None
            locale = redis_dict['locale'.encode('utf-8')] if 'locale'.encode('utf-8') in redis_dict else None

            result = schemas.SearchResult(
                            id=f"{redis_path}_{redis_tag}", 
                            title = title,
                            description = description,
                            path = f"{redis_path}#{redis_tag}",
                            locale = locale
                        )
            results.append(result)

        answer, referencies = utils.generate_answer(question, top_results[question], deps.db.connection, top_links = utils.TOP_LINKS)
        #answer = " "
        answers.append(f"{question}\n {answer}")
        links.append(" ".join(referencies))

    return schemas.SearchResultFull(results=results,
                                    answers=answers,
                                    links = links,
                                    questions = questions,
                                    totalHits = len(results)
    )
