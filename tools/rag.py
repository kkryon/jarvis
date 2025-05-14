from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import os

class RAGAgent:
    def __init__(self, persist_dir='vectorstore', docs_dir='docs', embed_model='all-MiniLM-L6-v2', top_k=2):
        self.collection = self._init_vector_store(persist_dir)
        self.embed_model = SentenceTransformer(embed_model)
        self.top_k = top_k
        # ... (rest of implementation)