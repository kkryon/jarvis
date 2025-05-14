from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2B. FILE SYSTEM AGENT
# ────────────────────────────────────────────────────────────────────────
class FileSystemAgent(Agent):
    """Agent for interacting with the file system."""

    @property
    def tool_schema(self) -> Dict[str, Any]:
        """Get the schema defining the file system agent's capabilities.
        
        Returns:
            Dict[str, Any]: Schema for file system tools
        """
        return {
            "name": "file_system",
            "description": "Interact with the file system for reading, writing, and listing files",
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read the contents of a specified file within the workspace",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file to be read"
                        }
                    },
                    "required": ["path"]
                },
                {
                    "name": "write_file",
                    "description": "Write (or overwrite) content to a specified file within the workspace",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file to be written"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write into the file"
                        }
                    },
                    "required": ["path", "content"]
                },
                {
                    "name": "list_dir",
                    "description": "List files and directories in a given path within the workspace",
                    "parameters": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the directory to list. Defaults to '.' (current directory).",
                            "default": "."
                        }
                    },
                    "required": []
                }
            ]
        }

    def __init__(self, **kwargs):
        """Initialize file system agent with orchestrator reference."""
        super().__init__(**kwargs)
        print("FileSystemAgent initialized")

    def read_file(self, path: str) -> str:
        """Read the contents of a file."""
        abs_path = Path(path).resolve()
        # Basic sandboxing: prevent reading files outside the workspace (or a designated 'safe' area)
        # For this example, we assume the agent runs in a workspace, and shouldn't go above it.
        # A more robust solution would be needed for a production system.
        try:
            workspace_root = Path(os.getcwd()).resolve()
            if not abs_path.is_relative_to(workspace_root): # Python 3.9+
                 # Fallback for older Python:
                 # if workspace_root not in abs_path.parents and abs_path != workspace_root:
                 return f"[Error: File path '{path}' is outside the allowed workspace.]"
        except AttributeError: # Older python without is_relative_to
             pass # Skip check for older python for now, or implement a more complex one

        try:
            return abs_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"[Error: File not found at '{path}']"
        except Exception as e:
            return f"[Error reading file '{path}': {e}]"

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file. Overwrites if exists."""
        abs_path = Path(path).resolve()
        try:
            workspace_root = Path(os.getcwd()).resolve()
            # Similar sandboxing for writing
            if not abs_path.is_relative_to(workspace_root):
                 return f"[Error: File path '{path}' is outside the allowed workspace for writing.]"
        except AttributeError:
            pass

        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            abs_path.write_text(content, encoding="utf-8")
            return f"[File written successfully: {path}]"
        except Exception as e:
            return f"[Error writing file '{path}': {e}]"

    def list_dir(self, path: str = ".") -> str:
        """List files and directories in a given path, relative to workspace."""
        abs_path = (Path(os.getcwd()) / path).resolve()
        try:
            workspace_root = Path(os.getcwd()).resolve()
            if not abs_path.is_relative_to(workspace_root) and abs_path != workspace_root:
                 return f"[Error: Directory path '{path}' is outside the allowed workspace.]"
        except AttributeError:
            pass
        
        if not abs_path.is_dir():
            return f"[Error: '{path}' is not a valid directory or is outside the workspace.]"
        try:
            files = [f.name for f in abs_path.iterdir()]
            return "\\n".join(files) if files else "[Directory is empty]"
        except Exception as e:
            return f"[Error listing directory '{path}': {e}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a specified file within the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to the file to be read."}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write (or overwrite) content to a specified file within the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to the file to be written."},
                        "content": {"type": "string", "description": "The content to write into the file."}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_dir",
                "description": "List files and directories in a given path within the workspace (defaults to current directory).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the directory to list. Defaults to '.' (current directory).",
                            "default": "."
                        }
                    },
                    "required": [] # Path is optional with default
                }
            }
        ]