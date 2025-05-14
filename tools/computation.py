import math
import re

class ComputationAgent:
    def calculate(self, expression):
        try:
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith('__')}
            if re.search(r"[a-zA-Z_]{2,}", expression) and not all(token in allowed_names or token.isdigit() or token in '-+/*()., ' for token in re.split(r"([()\s.,*/+-])", expression) if token):
                return "[Error: Expression contains potentially unsafe elements]"
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"[Error: {e}]"