import os
import subprocess
from jarvis.agents.base import Agent
from typing import Dict, Any

class SystemEnvironmentAgent(Agent):
    def get_env(self, var_name: str) -> str:
        return os.getenv(var_name, f"[Environment variable '{var_name}' not found]")

    def run_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"[Command failed with error: {e}]"
        except Exception as e:
            return f"[System command error: {e}]"

    def get_tool_json_schemas(self) -> list:
        return [{
            "name": tool,
            "description": desc,
            "parameters": params
        } for tool, desc, params in [
            ("get_env", "Retrieve the value of a system environment variable", {
                "type": "object",
                "properties": {
                    "var_name": {"type": "string"}
                },
                "required": ["var_name"]
            }),
            ("run_command", "Execute a shell command and return its output", {
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            })
        ]]