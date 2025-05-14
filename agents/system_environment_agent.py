from __future__ import annotations

import os
import re
import subprocess
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2H. SYSTEM & ENVIRONMENT AGENT
# ────────────────────────────────────────────────────────────────────────
class SystemEnvironmentAgent(Agent):
    """Agent for system and environment interactions."""
    def get_env(self, var_name: str) -> str:
        """Get the value of an environment variable."""
        print(f"SystemEnvironmentAgent: Getting env variable '{var_name}'")
        value = os.environ.get(var_name)
        return f"[Value of '{var_name}': {value}]" if value is not None else f"[Environment variable '{var_name}' not set]"

    def run_command(self, command: str) -> str:
        """
        Run a shell command and return its output.
        WARNING: This tool is powerful and can be dangerous if not used carefully.
        Commands are run within the agent's environment. Only use for safe, simple commands.
        Avoid commands that are interactive, long-running without backgrounding, or modify the system state undesirably.
        A timeout of 30 seconds is enforced.
        """
        if not command.strip():
            return "[Error: No command provided to run_command]"

        # Extremely basic safety check - this is NOT a comprehensive security measure.
        # A real system needs proper sandboxing, allow/deny lists, or user confirmation for commands.
        print(f"SystemEnvironmentAgent: Preparing to run command: '{command}'")
        restricted_patterns = [r"rm -rf", r"mkfs", r":(){:|:&};:", r"shutdown", r"reboot", r"wget", r"curl "] # Added wget/curl as example
        # Allow some common, relatively safe commands explicitly if needed, or deny by default.
        # For now, just a simple blocklist.
        for pattern in restricted_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return f"[Error: Command '{command}' matches a restricted pattern and was blocked for safety.]"
        
        try:
            print(f"SystemEnvironmentAgent: Executing command: '{command}'")
            # Use shell=True with caution. Consider splitting command for shell=False if possible.
            # Here, shell=True is used for simplicity with complex commands, but adds risk.
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, check=False)
            
            output = result.stdout.strip()
            error = result.stderr.strip()

            if result.returncode == 0:
                return f"[Command '{command}' executed successfully]\nOutput:\n{output}" if output else f"[Command '{command}' executed successfully with no output]"
            else:
                err_msg = f"[Command '{command}' failed with code {result.returncode}]"
                if error: err_msg += f"\nError Output:\n{error}"
                if output: err_msg += f"\nStandard Output (if any):\n{output}"
                return err_msg
        except subprocess.TimeoutExpired:
            return f"[Error: Command '{command}' timed out after 30 seconds.]"
        except Exception as e:
            return f"[Error running command '{command}': {type(e).__name__} - {e}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_env",
                "description": "Get the value of a system environment variable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "var_name": {"type": "string", "description": "The name of the environment variable to retrieve."}
                    },
                    "required": ["var_name"]
                }
            },
            {
                "name": "run_command",
                "description": "Run a shell command and return its output. WARNING: Use with extreme caution. Avoid interactive or system-modifying commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command to execute (e.g., \"ls -la\", \"echo \\'hello\\'\")."}
                    },
                    "required": ["command"]
                }
            }
        ]