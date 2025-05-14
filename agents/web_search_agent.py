from __future__ import annotations

import requests
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2A. DUCKDUCKGO WEB SEARCH AGENT
# ────────────────────────────────────────────────────────────────────────
class WebSearchAgent(Agent):
    """Agent for performing web searches."""
    def web_search(self, query: str, k: int = 5) -> str:
        """Query the local DuckDuckGo search server and return formatted results."""
        server_url = None
        try:
            with open('search_server_port.txt', 'r') as f:
                port = f.read().strip()
            server_url = f"http://localhost:{port}"
        except FileNotFoundError:
            # Try the default port defined in run_search_server.sh if file not found
            # This assumes the server might be running independently on a known default.
            # A more robust solution might involve service discovery or configuration.
             print("WebSearchAgent: search_server_port.txt not found, trying default port 7823.")
             server_url = "http://localhost:7823" # Default port

        print(f"WebSearchAgent: Searching for '{query}' (top {k} results) via {server_url}")
        try:
            resp = requests.get(server_url, params={"query": query, "k": k}, timeout=10)
            resp.raise_for_status()
            results = resp.json()
            if not results:
                return "[No web search results found.]"
            return "\\n".join(f"- {r['title']} ({r['url']})\\n  {r['snippet']}" for r in results)
        except requests.exceptions.ConnectionError:
            return f"[Web search error: Could not connect to the search server at {server_url}. Ensure it is running.]"
        except Exception as e:
            return f"[Web search error: {e}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "web_search",
                "description": "Search the web for real-time information using DuckDuckGo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        },
                        "k": {
                            "type": "integer",
                            "description": "Optional number of results to return (default is 5).",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        ]