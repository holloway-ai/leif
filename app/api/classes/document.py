from typing import List, Union

from app.api import deps, llm
from app.schemas import Document, DocumentUpdate

import lxml.html
import numpy as np
import re

class DocumentDB:
    def __init__(self, jdoc: Union[Document, DocumentUpdate], path: str = None):
        if isinstance(jdoc, Document):
            self.path = jdoc.path
            self.locale = jdoc.localeCode
            self.title = jdoc.title
            self.description = jdoc.description
            self.render = jdoc.render
        elif isinstance(jdoc, DocumentUpdate):
            self.path = path
            self.locale = jdoc.localeCode
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

    def extract_info_blocks( self ):
        parsed_html = lxml.html.fromstring( self.render )
        elements = parsed_html.xpath("//*")
        result = []
        current_block = DocumentBlock(  render_id= 'undefined', 
                                        text= '', 
                                        chunk_num= 0,
                                        content= 0,
                                        path= self.path,
                                        title= self.title,
                                        locale= self.locale
                                    )
        for element in elements:
            render_id = element.attrib.get('id', 'undefined')
            text_parts = [node.strip() for node in element.xpath("text()") if node.strip()]
            cleaned_text = " ".join(text_parts)
            cleaned_text = re.sub(r'[\n¶]', ' ', cleaned_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

            if cleaned_text:
                if render_id.startswith('p') or render_id == 'undefined':
                    current_block.text += '. ' + cleaned_text
                    current_block.content = 1 if current_block.text else 0
                else:
                    if current_block.text:
                        if len(current_block.text) > self.THRESHOLD :
                            texts = self.split_text(current_block.text )
                            for txt in texts:
                                current_block.text = txt
                                result.append(current_block)
                                current_block.chunk_num += 1
                        else:
                            result.append(current_block)
                    current_block =  DocumentBlock( render_id = render_id, 
                                                    text = cleaned_text + ' ', 
                                                    chunk_num= 0,
                                                    content= 0,
                                                    path= self.path,
                                                    title= self.title,
                                                    locale= self.locale
                                                    )
        if current_block.text:
            if len(current_block.text) > self.THRESHOLD :
                texts = self.split_text(current_block.text )
                for txt in texts:
                    current_block.text = txt
                    result.append(current_block)
                    current_block.chunk_num += 1
            else:
                result.append(current_block)

        return result
    

class DocumentBlock():
    def __init__(self, path: str, title: str, render_id: str, chunk_num: int, text: str, content: int, locale: str):
        self.path = path
        self.title = title
        self.render_id =render_id
        self.chunk_num = chunk_num
        self.text = text
        self.content = content
        self.locale = locale
        self.vector: List[float] = []
    
        self.COHERE_MODEL = llm.COHERE_MODEL
        
    def get_block_embedding(self):
         self.vector = deps.db.embedding.embed(texts=[self.text],  model=self.COHERE_MODEL).embeddings[0]
         self.vector = np.array(self.vector).astype(np.float32)
         return self.vector
    
    def get_block_dict(self, vector_embed):
        self.get_block_embedding()
        document_metadata = vars(self)
        if vector_embed != 'vector':
            document_metadata[vector_embed] = document_metadata['vector'].tobytes()
            del document_metadata['vector']
        return document_metadata