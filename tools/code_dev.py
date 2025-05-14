import subprocess
import pylint.lint
from io import StringIO
import black
from jarvis.agents.base import Agent
from typing import Dict, Any

class CodeDevelopmentAgent(Agent):
    def run_code(self, code: str) -> str:
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except Exception as e:
            return f"[Code execution error: {e}]"

    def lint_code(self, code: str) -> str:
        try:
            # Create a temporary file to hold the code
            with open("temp.py", "w") as f:
                f.write(code)
            # Run pylint
            pylint_output = StringIO()
            pylint.lint.Run(["temp.py"], exit=False, reporter=TextReporter(pylint_output))
            return pylint_output.getvalue()
        except Exception as e:
            return f"[Code linting error: {e}]"

    def format_code(self, code: str) -> str:
        try:
            return black.format_str(code, mode=black.FileMode())
        except Exception as e:
            return f"[Code formatting error: {e}]"

    def get_tool_json_schemas(self) -> list:
        return [{
            "name": tool,
            "description": desc,
            "parameters": params
        } for tool, desc, params in [
            ("run_code", "Execute Python code in a sandboxed environment", {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            }),
            ("lint_code", "Check Python code for errors and style issues", {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            }),
            ("format_code", "Format Python code according to PEP8 style guide", {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            })
        ]]