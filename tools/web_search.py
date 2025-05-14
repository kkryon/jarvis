import requests
import json
from jarvis.agents.base import Agent

class WebSearchAgent(Agent):
    def web_search(self, query, k=5):
        try:
            port = open('search_server_port.txt').read().strip()
            server_url = f"http://localhost:{port}"
        except FileNotFoundError:
            server_url = "http://localhost:7823"
        try:
            resp = requests.get(server_url, params={"query": query, "k": k}, timeout=10)
            resp.raise_for_status()
            results = resp.json()
            return "\n".join(f"- {r['title']} ({r['url']})\n  {r['snippet']}" for r in results)
        except Exception as e:
            return f"[Web search error: {e}]"