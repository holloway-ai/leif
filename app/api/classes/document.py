from typing import List, Union

from app.api import deps, llm
from app.schemas import Document, DocumentUpdate

import lxml.html
import numpy as np
import re
import copy

class DocumentDB():
    def __init__(self, jdoc: Union[Document, DocumentUpdate], id: str = None):
        if isinstance(jdoc, Document):
            self.doc_id = jdoc.id
            self.path = jdoc.path
            self.locale = jdoc.locale
            self.title = jdoc.title
            self.description = jdoc.description
            self.render = jdoc.render

        elif isinstance(jdoc, DocumentUpdate):
            self.doc_id = id
            self.path = jdoc.path
            self.locale = jdoc.locale
            self.title = jdoc.title
            self.description = jdoc.description
            self.render = jdoc.render
        else:
            raise TypeError("jdoc must be an instance of Document or DocumentUpdate.")
        
        self.THRESHOLD = int( 512/3 * 6 )

    def split_text(self, text):
        sentences = re.split('(?<=[.!?])\s', text)
        blocks = []
        current_block = ''

        for sentence in sentences:
            if len(current_block + sentence) <= self.THRESHOLD:
                current_block += sentence
            else:
                blocks.append(current_block)
                current_block = sentence

        blocks.append(current_block)
        return blocks

    def extract_info_blocks(self):
        dict_blocks = llm.extract_info_blocks(self)
        return [DocumentBlock(**block) for block in dict_blocks]
    
    def extract_info_blocks_with_vectors( self ):
        blocks = self.extract_info_blocks()
        blocks_texts = [ block.text for block in blocks]
        vectors = llm.get_embedding(blocks_texts)
        
        for ind, block in enumerate(blocks) :
            block.vector = vectors[ind]

        return blocks

class DocumentBlock():
    def __init__(self, doc_id: str, path: str, title: str, render_id: str, chunk_num: int, text: str, content: int, locale: str):
        self.path = path
        self.doc_id = doc_id
        self.title = title
        self.render_id =render_id
        self.chunk_num = chunk_num
        self.text = text
        self.content = content
        self.locale = locale
        self.vector: List[float] = []
            
    def get_block_embedding( self ):
         self.vector =  llm.get_embedding([self.text]) 
         return self.vector
    
    def get_block_dict(self, vector_embed, get_vectors = False):
        if get_vectors:
            self.get_block_embedding()

        document_metadata = vars(self)
        if vector_embed != 'vector':
            document_metadata[vector_embed] = document_metadata['vector']
            del document_metadata['vector']

        document_metadata[vector_embed] = np.array( document_metadata[vector_embed] ).astype(np.float32).tobytes()
        
        return document_metadata
