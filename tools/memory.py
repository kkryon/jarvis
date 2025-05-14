from jarvis.agents.base import Agent
import json
from typing import Dict, Any

class ConversationMemoryAgent(Agent):
    def __init__(self):
        self.memory: Dict[str, Any] = {}

    def save_memory(self, key: str, value: Any) -> str:
        self.memory[key] = value
        return f"[Memory saved: {key}]"

    def recall_memory(self, key: str) -> str:
        return json.dumps(self.memory.get(key, "[Memory not found]"))

    def list_memory_keys(self) -> str:
        return json.dumps(list(self.memory.keys()))

    def clear_memory_key(self, key: str) -> str:
        if key in self.memory:
            del self.memory[key]
            return f"[Memory cleared: {key}]"
        return f"[Memory key {key} not found]"

    def clear_all_memory(self) -> str:
        self.memory.clear()
        return "[All memory cleared]"

    def get_tool_json_schemas(self) -> list:
        return [{
            "name": tool,
            "description": "Manage conversation memory",
            "parameters": params
        } for tool, params in {
            "save_memory": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["key", "value"]
            },
            "recall_memory": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            },
            "list_memory_keys": {},
            "clear_memory_key": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            },
            "clear_all_memory": {}
        }.items()]