from __future__ import annotations
from typing import List, Dict, Any

# ────────────────────────────────────────────────────────────────────────
# 0A. BASE AGENT CLASS
# ────────────────────────────────────────────────────────────────────────
class Agent:
    """Base class for all specialized agents."""
    def __init__(self, orchestrator=None): # Removed llm_model, llm_tokenizer
        # self.llm_model = llm_model
        # self.llm_tokenizer = llm_tokenizer
        self.orchestrator = orchestrator

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with provided arguments and return its result."""
        if hasattr(self, tool_name) and callable(getattr(self, tool_name)):
            method = getattr(self, tool_name)
            try:
                # Arguments are already a dict from the orchestrator
                return method(**arguments)
            except TypeError as e:
                return f"[Error: Incorrect arguments for tool {tool_name}. Expected: {method.__annotations__}. Detail: {e}]"
            except Exception as e:
                return f"[Error executing tool {tool_name}: {e}]"
        return f"[Error: Tool '{tool_name}' not found in agent {self.__class__.__name__}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        """Return a list of JSON schema definitions for the tools this agent provides."""
        # To be implemented by subclasses
        return [] 