from __future__ import annotations

import json
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2I. CONVERSATION & MEMORY AGENT
# ────────────────────────────────────────────────────────────────────────
class ConversationMemoryAgent(Agent):
    """Agent for managing short-term conversation memory and recalling long-term conversation history."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.memory: Dict[str, Any] = {} # Simple key-value store for short-term memory

    def save_memory(self, key: str, value: Any) -> str:
        """Save a piece of information (value can be string, number, list, dict) for later use in the conversation under a given key."""
        # Potentially serialize complex types if needed, or store as is if JSON serializable by the LLM
        try:
            # Attempt to see if value is JSON-serializable for consistency with LLM expectations
            # This doesn't change how it's stored here, just a check.
            json.dumps(value) 
            self.memory[key] = value
            return f"[Memory saved for key: '{key}'. Value: {str(value)[:100]}{ '...' if len(str(value)) > 100 else '' }]"
        except TypeError:
            return f"[Error: Value for key '{key}' is not JSON serializable. Cannot save to memory.]"


    def recall_memory(self, key: str) -> str:
        """Retrieve a previously saved piece of information from the conversation memory using its key."""
        value = self.memory.get(key)
        if value is not None:
            # LLM expects a string back.
            return f"[Recalled memory for key '{key}': {json.dumps(value)}]"
        return f"[Memory not found for key: '{key}']"

    def list_memory_keys(self) -> str:
        """List all keys currently stored in the conversation memory."""
        if not self.memory:
            return "[Conversation memory is currently empty]"
        return "[Available memory keys:\n" + "\n".join(f"- {key}" for key in self.memory.keys()) + "]"

    def clear_memory_key(self, key: str) -> str:
        """Clear a specific key-value pair from the conversation memory."""
        if key in self.memory:
            del self.memory[key]
            return f"[Memory cleared for key: '{key}']"
        return f"[Memory key '{key}' not found, nothing to clear]"

    def clear_all_memory(self) -> str:
        """Clear all items from the conversation memory."""
        self.memory.clear()
        return "[All conversation memory has been cleared]"

    # --- Long-term semantic recall method (new) ---
    def recall_past_interaction_semantically(self, query_text: str, user_id_filter: str | None = None, num_results: int = 3) -> str:
        """Search through long-term conversation history for interactions semantically similar to the query text."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available for recalling past interactions.]"
        
        # user_id_filter can be used if we want to explicitly filter by a user ID other than the default
        # or if the MemoryManager's default_user_id is not appropriate for this specific recall.
        # For now, recall_relevant_interactions in MemoryManager will use its default_user_id if user_id_filter is None.
        
        print(f"ConversationMemoryAgent: Recalling past interactions via MemoryManager for query: '{query_text[:50]}...'")
        results = self.orchestrator.memory_manager.recall_relevant_interactions(
            query_text=query_text,
            user_id=user_id_filter, # This allows overriding the default user in MemoryManager if needed
            n_results=num_results
        )

        if not results:
            return "[No relevant past interactions found for the query via MemoryManager.]"

        # Format results for the LLM
        # Each result is a dict with 'interaction', 'metadata', 'distance'
        formatted_results = []
        for res in results:
            interaction_text = res.get('interaction', '[Interaction text not available]')
            metadata = res.get('metadata', {})
            timestamp = metadata.get('timestamp', '[timestamp not available]')
            # uid = metadata.get('user_id', '[user_id not available]') # User ID is part of the interaction string already
            formatted_results.append(f"- Interaction (Timestamp: {timestamp}):\n  \"{interaction_text}\"")
        
        return "[Relevant past interactions found:\n" + "\n".join(formatted_results) + "]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        existing_schemas = [
            {
                "name": "save_memory",
                "description": "Save a piece of information (key-value pair) for later use in the current conversation. Value should be JSON serializable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The unique key under which to save the information."},
                        "value": {"type": [ "string", "number", "boolean", "array", "object" ], "description": "The information (value) to save. Must be JSON serializable."}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "recall_memory",
                "description": "Retrieve a previously saved piece of information from the conversation memory using its key.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key of the information to retrieve."}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "list_memory_keys",
                "description": "List all keys currently stored in the conversation memory.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "clear_memory_key",
                "description": "Clear a specific key-value pair from the conversation memory.",
                 "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key of the memory item to clear."}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "clear_all_memory",
                "description": "Clear all items from the conversation memory.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        ]
        
        new_schemas = [
             {
                "name": "recall_past_interaction_semantically",
                "description": "Search through persistent long-term conversation history for interactions semantically similar to the query text. Useful for remembering details from previous conversations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {
                            "type": "string",
                            "description": "The query or topic to search for in past conversation history."
                        },
                        "user_id_filter": {
                            "type": ["string", "null"],
                            "description": "Optional. Filter results for a specific user ID. If null or not provided, defaults to the current primary user context.",
                            "default": None
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of relevant interactions to retrieve.",
                            "default": 3
                        }
                    },
                    "required": ["query_text"]
                }
            }
        ]
        return existing_schemas + new_schemas