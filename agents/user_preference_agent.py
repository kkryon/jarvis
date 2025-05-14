from __future__ import annotations

from typing import List, Dict, Any, Optional

from agents.base_agent import Agent

class UserPreferenceAgent(Agent):
    """Agent for managing persistent user preferences via the MemoryManager."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not (self.orchestrator and self.orchestrator.memory_manager):
            print("[CRITICAL] UserPreferenceAgent: Orchestrator or MemoryManager not available during init. This agent will not function.")
            # Potentially raise an error or set a disabled state

    def store_user_preference(self, key: str, value: str, user_id: Optional[str] = None) -> str:
        """Stores a persistent preference for a user. If user_id is not provided, uses the default session user."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot store preference.]"
        
        success = self.orchestrator.memory_manager.store_preference(key, value, user_id=user_id)
        if success:
            uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
            return f"[Preference '{key}' saved for user '{uid}'.]"
        return f"[Error: Failed to store preference '{key}'.]"

    def get_user_preference(self, key: str, user_id: Optional[str] = None) -> str:
        """Retrieves a persistent preference for a user. If user_id is not provided, uses the default session user."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot get preference.]"
        
        value = self.orchestrator.memory_manager.get_preference(key, user_id=user_id)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if value is not None:
            return f"[Preference for user '{uid}', key '{key}': {value}]"
        return f"[No preference found for user '{uid}', key '{key}'.]"

    def get_all_user_preferences(self, user_id: Optional[str] = None) -> str:
        """Retrieves all persistent preferences for a user. If user_id is not provided, uses the default session user."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot get all preferences.]"

        preferences = self.orchestrator.memory_manager.get_all_preferences(user_id=user_id)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if preferences is not None:
            if not preferences: # Empty dict
                return f"[No preferences found for user '{uid}'.]"
            # Format as a string for the LLM
            prefs_str = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
            return f"[Preferences for user '{uid}':\n{prefs_str}]"
        return f"[Error: Could not retrieve preferences for user '{uid}'.]"

    def delete_user_preference(self, key: str, user_id: Optional[str] = None) -> str:
        """Deletes a persistent preference for a user. If user_id is not provided, uses the default session user."""
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot delete preference.]"
        
        success = self.orchestrator.memory_manager.delete_preference(key, user_id=user_id)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if success:
            return f"[Preference '{key}' deleted for user '{uid}'.]"
        return f"[Error: Failed to delete preference '{key}' for user '{uid}', or key not found.]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "store_user_preference",
                "description": "Stores a persistent preference (key-value pair) for a user. This information will be remembered across sessions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key for the preference (e.g., 'favorite_color', 'city')."},
                        "value": {"type": "string", "description": "The value of the preference (e.g., 'blue', 'New York')."},
                        "user_id": {"type": ["string", "null"], "description": "Optional. Specific user ID. Defaults to current session user if not provided.", "default": None}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "get_user_preference",
                "description": "Retrieves a specific persistent preference for a user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key of the preference to retrieve."},
                        "user_id": {"type": ["string", "null"], "description": "Optional. Specific user ID. Defaults to current session user if not provided.", "default": None}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "get_all_user_preferences",
                "description": "Retrieves all persistent preferences for a user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": ["string", "null"], "description": "Optional. Specific user ID. Defaults to current session user if not provided.", "default": None}
                    },
                    "required": [] # user_id is optional, will use default context if not given
                }
            },
            {
                "name": "delete_user_preference",
                "description": "Deletes a specific persistent preference for a user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key of the preference to delete."},
                        "user_id": {"type": ["string", "null"], "description": "Optional. Specific user ID. Defaults to current session user if not provided.", "default": None}
                    },
                    "required": ["key"]
                }
            }
        ] 