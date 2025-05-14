from pathlib import Path
import datetime
import json

# Assuming structured_store.py and vector_store.py are in the same directory or accessible
from .structured_store import StructuredMemory, DEFAULT_DB_PATH
from .vector_store import VectorStore, DEFAULT_CHROMA_PATH, DEFAULT_DOC_COLLECTION_NAME, DEFAULT_CONVO_COLLECTION_NAME
from .embedding_utils import DEFAULT_EMBEDDING_MODEL # For awareness of the model being used

# Attempt to import DEBUG from core.config
# This might require adjustments based on how this module is run/imported relative to the core package.
try:
    from core.config import DEBUG
except ImportError:
    # Fallback if core.config is not directly accessible (e.g., running this module standalone)
    # You might want a more robust way to handle this if memory_manager can be run independently of the main app.
    print("[WARN] MemoryManager: Could not import DEBUG from core.config. Debug prints will be disabled for this module.")
    DEBUG = False

# Default user ID if not specified (can be configured or passed by the agent)
DEFAULT_USER_ID = "default_user"

class MemoryManager:
    """
    Orchestrates different types of memory storage and retrieval for the agent,
    combining structured (SQLite) and vector (ChromaDB) stores.
    """

    def __init__(
        self,
        user_id: str = DEFAULT_USER_ID,
        db_path: str | Path | None = None, # For StructuredMemory
        chroma_path: str | Path | None = None, # For VectorStore
        doc_collection_name: str = DEFAULT_DOC_COLLECTION_NAME,
        convo_collection_name: str = DEFAULT_CONVO_COLLECTION_NAME,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    ):
        """
        Initializes the MemoryManager, which in turn initializes StructuredMemory and VectorStore.

        Args:
            user_id: The primary user ID this memory manager instance will operate for (can be overridden per call).
            db_path: Path to the SQLite database file for structured memory.
            chroma_path: Path to the ChromaDB persistence directory for vector memory.
            doc_collection_name: ChromaDB collection name for documents.
            convo_collection_name: ChromaDB collection name for conversations.
            embedding_model_name: Sentence embedding model to be used by VectorStore.
        """
        self.default_user_id = user_id
        
        # Initialize Structured Memory (SQLite for preferences, facts)
        self.structured_memory = StructuredMemory(db_path=db_path)
        print(f"StructuredMemory initialized with db: {self.structured_memory.db_path}")

        # Initialize Vector Store (ChromaDB for documents, conversations)
        self.vector_store = VectorStore(
            chroma_path=chroma_path if chroma_path else DEFAULT_CHROMA_PATH,
            doc_collection_name=doc_collection_name,
            convo_collection_name=convo_collection_name,
            embedding_model_name=embedding_model_name
        )
        print(f"VectorStore initialized. Embedding model: {embedding_model_name}")
        print(f"  Document Collection: '{self.vector_store.doc_collection_name}' at '{self.vector_store.chroma_path}'")
        print(f"  Conversation Collection: '{self.vector_store.convo_collection_name}' at '{self.vector_store.chroma_path}'")

    # --- User Preference Methods (via StructuredMemory) ---
    def store_preference(self, key: str, value: str, user_id: str | None = None) -> bool:
        uid = user_id if user_id else self.default_user_id
        return self.structured_memory.store_preference(key, value, user_id=uid)

    def get_preference(self, key: str, user_id: str | None = None) -> str | None:
        uid = user_id if user_id else self.default_user_id
        return self.structured_memory.get_preference(key, user_id=uid)

    def get_all_preferences(self, user_id: str | None = None) -> dict[str, str] | None:
        uid = user_id if user_id else self.default_user_id
        return self.structured_memory.get_all_preferences(user_id=uid)

    def delete_preference(self, key: str, user_id: str | None = None) -> bool:
        uid = user_id if user_id else self.default_user_id
        return self.structured_memory.delete_preference(key, user_id=uid)

    # --- Document Knowledge Base Methods (via VectorStore) ---
    def add_document(self, doc_text: str, metadata: dict | None = None, doc_id: str | None = None) -> bool:
        """Adds a single document text to the knowledge base."""
        # VectorStore expects lists, so we wrap the single items
        metadatas_list = [metadata] if metadata else None
        ids_list = [doc_id] if doc_id else None
        return self.vector_store.add_documents([doc_text], metadatas=metadatas_list, ids=ids_list)

    def add_documents_batch(self, doc_texts: list[str], metadatas: list[dict] | None = None, ids: list[str] | None = None) -> bool:
        """Adds a batch of document texts to the knowledge base."""
        return self.vector_store.add_documents(doc_texts, metadatas=metadatas, ids=ids)

    def query_knowledge_base(self, query_text: str, n_results: int = 3, filter_metadata: dict | None = None) -> list[dict]:
        """
        Queries the document knowledge base for relevant information.

        Returns:
            A list of result dictionaries, each containing 'document', 'metadata', 'distance'.
            Returns an empty list if no results or an error occurs.
        """
        results = self.vector_store.query_documents(query_text, n_results=n_results, where_filter=filter_metadata)
        if results and results.get('documents') and results.get('metadatas') and results.get('distances'):
            # Chroma returns lists of lists for these items, even for a single query_text
            # We simplify it for the MemoryManager API user
            return [
                {"document": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0])
            ]
        return []

    # --- Conversation History Methods (via VectorStore) ---
    def log_interaction(self, user_utterance: str, agent_response: str, user_id: str | None = None, convo_id: str | None = None, timestamp: str | None = None) -> bool:
        """
        Logs a user-agent interaction to the conversation history.
        """
        uid = user_id if user_id else self.default_user_id
        interaction_text = f"User ({uid}): {user_utterance}\nAgent: {agent_response}"
        
        ts = timestamp if timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        metadata = {"user_id": uid, "timestamp": ts}
        if convo_id:
            metadata["convo_id"] = convo_id # Optional: to group turns from the same conversation session

        return self.vector_store.add_conversation_history([interaction_text], metadatas=[metadata])

    def recall_relevant_interactions(self, query_text: str, user_id: str | None = None, n_results: int = 3, filter_metadata: dict | None = None) -> list[dict]:
        """
        Recalls relevant past interactions based on a query.
        If user_id is provided, it can be used in the metadata filter.

        Returns:
            A list of result dictionaries, each containing 'interaction', 'metadata', 'distance'.
            Returns an empty list if no results or an error occurs.
        """
        uid = user_id if user_id else self.default_user_id
        
        # Construct a filter that can include the user_id if needed
        final_filter = {"user_id": uid}
        if filter_metadata:
            final_filter.update(filter_metadata)
            
        if DEBUG:
            print(f"[DEBUG] MemoryManager.recall_relevant_interactions: Querying '{self.vector_store.convo_collection_name}' for: '{query_text[:100]}...' with filter: {final_filter}, n_results: {n_results}")
        results = self.vector_store.query_conversation_history(query_text, n_results=n_results, where_filter=final_filter)
        
        if DEBUG:
            print(f"[DEBUG] MemoryManager.recall_relevant_interactions: Raw results from vector store: {results}")

        if results and results.get('documents') and results.get('metadatas') and results.get('distances'):
            return [
                {"interaction": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0])
            ]
        return []

    def log_reasoning_trace(self, reasoning_messages: list[dict], trace_type: str, user_id: str | None = None, related_query: str | None = None, timestamp: str | None = None) -> bool:
        """
        Logs a detailed reasoning trace (e.g., internal dialogue of a reasoning LLM)
        into the conversation history store.
        """
        uid = user_id if user_id else self.default_user_id
        ts = timestamp if timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            trace_content = json.dumps(reasoning_messages, indent=2)
        except TypeError:
            if DEBUG: # Make this warning conditional
                print(f"[WARN] MemoryManager.log_reasoning_trace: Could not serialize reasoning_messages directly for trace_type '{trace_type}'. Storing as string representation.")
            trace_content = str(reasoning_messages)
            
        metadata = {
            "user_id": uid,
            "timestamp": ts,
            "trace_type": trace_type, # e.g., "memory_reasoner_dialogue"
            "content_type": "reasoning_trace_json" # To indicate the content is a JSON string of messages
        }
        if related_query:
            metadata["related_query"] = related_query

        # We are storing the JSON string of the messages list as a single "document" in the conversation history
        # The 'interaction' field in the recall_relevant_interactions will thus be this JSON string.
        # The tools consuming this will need to json.loads() it.
        if DEBUG:
            print(f"[DEBUG] MemoryManager: Logging reasoning trace. Type: {trace_type}, User: {uid}, Length: {len(trace_content)}")
        return self.vector_store.add_conversation_history([trace_content], metadatas=[metadata])

    def close(self):
        """Closes connections to underlying memory stores."""
        print("Closing MemoryManager connections...")
        self.structured_memory.close()
        # VectorStore (ChromaDB client) doesn't have an explicit close, it manages persistence.
        print("MemoryManager closed.")

    def __del__(self):
        self.close()

if __name__ == '__main__':
    print("Testing MemoryManager...")
    
    # Define test paths (ensure data and test_vectorstore dirs are writable/creatable)
    test_data_dir = Path(__file__).resolve().parent.parent / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    test_db_file = test_data_dir / "test_mm_prefs.db"

    test_chroma_dir = Path(__file__).resolve().parent.parent / "test_mm_vectorstore"

    # Clean up old test files/dirs before test
    if test_db_file.exists():
        import os
        os.remove(test_db_file)
    if test_chroma_dir.exists():
        import shutil
        shutil.rmtree(test_chroma_dir)
    # test_chroma_dir.mkdir(parents=True, exist_ok=True) # VectorStore will create it

    mm = MemoryManager(
        user_id="test_user_001",
        db_path=test_db_file,
        chroma_path=test_chroma_dir
    )

    # --- Test Preferences ---
    print("\n--- Testing Preferences ---")
    print(f"Store pref 'color'='blue': {mm.store_preference('color', 'blue')}")
    print(f"Get pref 'color': {mm.get_preference('color')}") # Expected: blue
    print(f"Store pref 'food'='pizza' for user 'user_002': {mm.store_preference('food', 'pizza', user_id='user_002')}")
    print(f"Get pref 'food' for 'user_002': {mm.get_preference('food', user_id='user_002')}") # Expected: pizza
    print(f"Get pref 'food' for default user: {mm.get_preference('food')}") # Expected: None

    # --- Test Knowledge Base ---
    print("\n--- Testing Knowledge Base ---")
    doc1_text = "The Earth revolves around the Sun."
    doc1_meta = {"source": "astronomy_basics", "category": "space"}
    print(f"Add document 1: {mm.add_document(doc1_text, doc1_meta, doc_id='earth_sun')}")

    doc2_text = "Mars is known as the Red Planet."
    doc2_meta = {"source": "planetary_facts", "category": "space"}
    print(f"Add document 2: {mm.add_document(doc2_text, doc2_meta, doc_id='mars_red')}")

    kb_query = "Tell me about planets."
    kb_results = mm.query_knowledge_base(kb_query, n_results=2)
    print(f"Knowledge query '{kb_query}':")
    for res in kb_results:
        print(f"  - Doc: \"{res['document'][:50]}...\", Meta: {res['metadata']}, Dist: {res['distance']:.4f}")
    
    # --- Test Conversation History ---
    print("\n--- Testing Conversation History ---")
    print(f"Log convo 1: {mm.log_interaction('Hello there', 'Hi, how are you?', convo_id='conv1')}")
    print(f"Log convo 2: {mm.log_interaction('What is the capital of France?', 'The capital is Paris.', user_id='user_002', convo_id='conv2')}")
    print(f"Log convo 3 for default user: {mm.log_interaction('Thanks for the info about Paris', 'You are welcome!', convo_id='conv2')}") # Note: convo_id reused, but user different from previous for conv2

    convo_query = "capital city"
    convo_results = mm.recall_relevant_interactions(convo_query, user_id="user_002", n_results=1)
    print(f"Conversation query '{convo_query}' for user 'user_002':")
    for res in convo_results:
        print(f"  - Interaction: \"{res['interaction'][:70]}...\", Meta: {res['metadata']}, Dist: {res['distance']:.4f}")

    convo_query_default = "hello"
    convo_results_default = mm.recall_relevant_interactions(convo_query_default, n_results=1) # Default user
    print(f"Conversation query '{convo_query_default}' for default user ({mm.default_user_id}):")
    for res in convo_results_default:
        print(f"  - Interaction: \"{res['interaction'][:70]}...\", Meta: {res['metadata']}, Dist: {res['distance']:.4f}")

    mm.close()

    # Clean up after test
    print("\n--- Cleaning up test files ---")
    if test_db_file.exists():
        import os
        os.remove(test_db_file)
        print(f"Removed {test_db_file}")
    if test_chroma_dir.exists():
        import shutil
        shutil.rmtree(test_chroma_dir)
        print(f"Removed {test_chroma_dir}")

    print("\nMemoryManager test complete.") 