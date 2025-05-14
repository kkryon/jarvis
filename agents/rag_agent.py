from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

# ChromaDB and SentenceTransformer imports are no longer needed here directly,
# as MemoryManager will handle those.
# from chromadb import Client
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

from agents.base_agent import Agent
from core.config import DOCS_DIR, RETRIEVAL_TOP_K # EMBED_MODEL, VECTOR_DIR no longer needed directly by RAGAgent for init

# ────────────────────────────────────────────────────────────────────────
# 2  VECTOR STORE + EMBEDDINGS AGENT (RAGAgent)
# ────────────────────────────────────────────────────────────────────────
class RAGAgent(Agent):
    """Agent for Retrieval Augmented Generation, using MemoryManager for backend."""
    def __init__(self, docs_dir: Path = DOCS_DIR, top_k: int = RETRIEVAL_TOP_K, **kwargs):
        super().__init__(**kwargs)
        # self.collection = self._init_vector_store(persist_dir) # Removed
        # self.embed_model_name = embed_model_name # Removed
        # self._embedder = None  # Removed
        self.top_k = top_k
        self.docs_dir = docs_dir # Store for potential re-indexing or other operations

        # Initial indexing is done once if the MemoryManager's document collection seems empty.
        # This relies on MemoryManager being initialized in Orchestrator before agents.
        if self.orchestrator and self.orchestrator.memory_manager:
            # Check if the specific document collection in MemoryManager is empty
            doc_collection_count = self.orchestrator.memory_manager.vector_store.get_document_collection_count()
            if doc_collection_count == 0:
                print(f"RAGAgent: MemoryManager's document collection ('{self.orchestrator.memory_manager.vector_store.doc_collection_name}') is empty.")
                new_docs_indexed = self.index_documents(self.docs_dir) # Pass docs_dir here
                if new_docs_indexed:
                    print(f"RAGAgent: Indexed {new_docs_indexed} new document(s) into MemoryManager's knowledge base.\n")
            else:
                print(f"RAGAgent: MemoryManager's document collection already contains {doc_collection_count} items. Skipping initial indexing by RAGAgent.")
        else:
            print("[WARN] RAGAgent: Orchestrator or MemoryManager not available during RAGAgent init. Document indexing might be skipped.")

    # def _init_vector_store(self, persist_dir: Path): # Removed
    #     client = Client(Settings(persist_directory=str(persist_dir), is_persistent=True))
    #     return client.get_or_create_collection(name="assistant_knowledge")

    # @property
    # def embedder(self): # Removed
    #     if self._embedder is None:
    #         self._embedder = SentenceTransformer(self.embed_model_name)
    #     return self._embedder

    def index_documents(self, docs_dir: Path) -> int:
        """Indexes documents from the specified directory into MemoryManager's document collection."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            print("RAGAgent: Orchestrator or MemoryManager not available. Cannot index documents.")
            return 0

        docs_texts: List[str] = []
        docs_metadatas: List[Dict[str, Any]] = []
        docs_ids: List[str] = []
        
        if not docs_dir.is_dir():
            print(f"RAGAgent: Docs directory {docs_dir} not found. Skipping indexing.")
            return 0
        
        doc_files = list(docs_dir.glob("*.txt"))
        if not doc_files:
            print(f"RAGAgent: No .txt files found in {docs_dir}. Nothing to index.")
            return 0

        for path in doc_files:
            try:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    docs_texts.append(text)
                    # Using filename as ID and part of metadata for traceability
                    docs_ids.append(path.name)
                    docs_metadatas.append({"source_filename": path.name, "indexed_by": "RAGAgent"})
            except Exception as e:
                print(f"RAGAgent: Error reading or processing file {path.name}: {e}")

        if not docs_texts:
            print("RAGAgent: No valid text content found in documents to index.")
            return 0
        
        print(f"RAGAgent: Attempting to add {len(docs_texts)} documents to MemoryManager's knowledge base...")
        # MemoryManager.add_documents_batch will handle embedding via VectorStore
        success = self.orchestrator.memory_manager.add_documents_batch(
            doc_texts=docs_texts,
            metadatas=docs_metadatas,
            ids=docs_ids
        )
        if success:
            print(f"RAGAgent: Successfully requested MemoryManager to add {len(docs_texts)} documents.")
            return len(docs_texts)
        else:
            print(f"RAGAgent: Failed to add documents via MemoryManager.")
            return 0

    def retrieve_relevant_docs(self, query: str) -> str:
        """Retrieve documents relevant to a query from the knowledge base via MemoryManager."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available for document retrieval.]"
        
        # Check if the document collection in MemoryManager is empty
        # This check can also be done within MemoryManager.query_knowledge_base if preferred
        if self.orchestrator.memory_manager.vector_store.get_document_collection_count() == 0:
            return "[Knowledge base (via MemoryManager) is empty. No documents to retrieve.]"
        
        print(f"RAGAgent: Retrieving documents via MemoryManager for query: '{query[:50]}...'")
        results = self.orchestrator.memory_manager.query_knowledge_base(
            query_text=query,
            n_results=self.top_k
            # We can add metadata filters here if needed, e.g., filter_metadata={"indexed_by": "RAGAgent"}
        )
        
        if not results:
            return "[No relevant documents found for the query via MemoryManager.]"
        
        # MemoryManager.query_knowledge_base returns a list of dicts
        # Each dict has 'document', 'metadata', 'distance'
        doc_strings = [result.get('document', '') for result in results]
        return "\n---\n".join(doc_strings)

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "retrieve_relevant_docs",
                "description": "Retrieve documents relevant to a query from the local knowledge base (RAG). This searches through previously indexed text files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents from the knowledge base."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]