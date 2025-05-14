import wikipedia
import arxiv
import requests
from jarvis.agents.base import Agent
from typing import List, Dict, Any

class KnowledgeToolsAgent(Agent):
    def search_wikipedia(self, query: str, max_results: int = 3) -> str:
        try:
            results = wikipedia.search(query, results=max_results)
            return "\n".join(f"- {title}: {wikipedia.summary(title, sentences=2)}" for title in results)
        except Exception as e:
            return f"[Wikipedia search error: {e}]"

    def search_arxiv(self, query: str, max_results: int = 3) -> str:
        try:
            results = arxiv.Search(query=query, max_results=max_results).results()
            return "\n".join(f"- {r.title} ({r.entry_id})\n  {r.summary}" for r in results)
        except Exception as e:
            return f"[arXiv search error: {e}]"

    def search_github(self, query: str, max_results: int = 3) -> str:
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            params = {"q": query, "per_page": max_results}
            resp = requests.get("https://api.github.com/search/repositories", 
                              headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json().get('items', [])
            return "\n".join(f"- {i['name']} ({i['html_url']})\n  {i['description']}" for i in items)
        except Exception as e:
            return f"[GitHub search error: {e}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [{
            "name": tool,
            "description": desc,
            "parameters": params
        } for tool, desc, params in [
            ("search_wikipedia", "Search Wikipedia for articles", {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            }),
            ("search_arxiv", "Search arXiv for academic papers", {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            }),
            ("search_github", "Search GitHub repositories", {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            })
        ]]