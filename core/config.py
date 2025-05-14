import re
from pathlib import Path
import os

# ────────────────────────────────────────────────────────────────────────
# 0  CONFIGURATION
# ────────────────────────────────────────────────────────────────────────
DOCS_DIR = Path("docs")               # directory containing .txt knowledge files
VECTOR_DIR = Path("vectorstore")      # Chroma persistence location
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_HISTORY_PAIRS = 15                # number of past user/assistant turns kept
RETRIEVAL_TOP_K = 2                   # number of docs fetched each turn
MAX_TOOL_ITERATIONS = 10000               # Max sequential tool calls per user turn

# Regex for parsing tool calls from LLM output
TOOL_CALL_PATTERN = re.compile(r"<tool_call>([\s\S]*?)</tool_call>")

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL_NAME = "" # As specified by user
OPENROUTER_SITE_URL = "http://localhost/agent" # Placeholder, replace with actual if available
OPENROUTER_SITE_NAME = ""      # Placeholder 

# Contextualizer LLM Configuration (for synthesizing memory context)
# Renaming and updating for the new Memory Reasoning LLM approach
MEMORY_REASONING_LLM_MODEL_NAME = "" 

# Debugging Flag
# Set JARVIS_DEBUG=true in your environment to enable debug prints
DEBUG = os.getenv("JARVIS_DEBUG", "False").lower() == "true"

# Placeholder for other configurations if any 