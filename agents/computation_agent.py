from __future__ import annotations

import math
import re
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2C. COMPUTATION AGENT
# ────────────────────────────────────────────────────────────────────────
class ComputationAgent(Agent):
    """Agent for mathematical calculations."""
    def calculate(self, expression: str) -> str:
        """Evaluate a mathematical expression using a safe eval."""
        try:
            # A more restricted eval environment
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_names.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow})
            
            # Simple check for potentially unsafe characters/patterns - not foolproof!
            if re.search(r"[a-zA-Z_]{2,}", expression) and not all(token in allowed_names or token.isdigit() or token in '-+/*()., ' for token in re.split(r"([()\s.,*/+-])", expression) if token):
                 return f"[Error: Expression '{expression}' contains potentially unsafe elements.]"

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"[Error calculating '{expression}': {e}]"

    # solve_equation placeholder remains, could be expanded with a library like SymPy
    def solve_equation(self, equation: str) -> str:
        return f"[Equation solver (e.g., for x in '2*x + 5 = 10') not robustly implemented. Equation: {equation}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "calculate",
                "description": "Evaluate a mathematical expression. Supports basic arithmetic and math functions (e.g., sin, cos, sqrt, log).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "The mathematical expression to evaluate (e.g., \"2 * (3 + 5)\", \"sqrt(16)\")."}
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "solve_equation",
                "description": "Solve a simple algebraic equation for one variable (placeholder).",
                 "parameters": {
                    "type": "object",
                    "properties": {
                        "equation": {"type": "string", "description": "The equation to solve (e.g., \"2*x + 5 = 10\")."}
                    },
                    "required": ["equation"]
                }
            }
        ]