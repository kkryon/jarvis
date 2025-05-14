from __future__ import annotations

import os
import ratelimit
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2E. KNOWLEDGE & RETRIEVAL AGENT (Placeholders)
# ────────────────────────────────────────────────────────────────────────
class KnowledgeToolsAgent(Agent):
    """Agent for accessing various knowledge sources including Wikipedia, arXiv, and GitHub."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize API clients
        self.wiki_api = None  # Lazy load
        self.github_client = None  # Lazy load
        self._init_github_client()
    
    def _init_github_client(self):
        """Initialize GitHub client if API key is available."""
        github_token = os.getenv('GITHUB_API_TOKEN')
        if github_token:
            try:
                from github import Github
                self.github_client = Github(github_token)
                print("KnowledgeToolsAgent: GitHub client initialized successfully.")
            except Exception as e:
                print(f"KnowledgeToolsAgent: Failed to initialize GitHub client: {e}")
        else:
            print("KnowledgeToolsAgent: GITHUB_API_TOKEN not set. GitHub search will be limited.")

    @property
    def wiki(self):
        """Lazy load Wikipedia API client."""
        if self.wiki_api is None:
            try:
                import wikipediaapi
                self.wiki_api = wikipediaapi.Wikipedia(
                    language='en',
                    extract_format=wikipediaapi.ExtractFormat.WIKI,
                    user_agent='JARVIS-AI-Agent/1.0'
                )
            except ImportError:
                print("KnowledgeToolsAgent: wikipedia-api package not installed.")
                return None
        return self.wiki_api

    @ratelimit.rate_limited(calls=30, period=60)  # 30 calls per minute
    def search_wikipedia(self, query: str, max_results: int = 3) -> str:
        """
        Search Wikipedia for articles matching the query.
        Returns formatted summaries of the top results.
        """
        if not self.wiki:
            return "[Error: Wikipedia API client not available. Please install wikipedia-api package.]"
        
        try:
            # Search for pages
            search_results = self.wiki.search(query, max_results=max_results)
            if not search_results:
                return f"[No Wikipedia articles found for query: '{query}']"
            
            # Format results
            formatted_results = []
            for title in search_results:
                page = self.wiki.page(title)
                if page.exists():
                    # Get summary (first paragraph)
                    summary = page.summary.split('\n')[0]
                    formatted_results.append(
                        f"- {title}\n"
                        f"  URL: {page.fullurl}\n"
                        f"  Summary: {summary[:300]}..."
                    )
            
            if not formatted_results:
                return f"[No Wikipedia articles found for query: '{query}']"
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"[Error searching Wikipedia: {str(e)}]"

    @ratelimit.rate_limited(calls=30, period=60)  # 30 calls per minute
    def search_arxiv(self, query: str, max_results: int = 3) -> str:
        """
        Search arXiv for academic papers matching the query.
        Returns formatted summaries of the top results.
        """
        try:
            import arxiv
            
            # Construct search query
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            # Format results
            formatted_results = []
            for result in search.results():
                # Format authors
                authors = ", ".join(author.name for author in result.authors)
                
                # Format categories
                categories = ", ".join(result.categories)
                
                # Format abstract (truncate if too long)
                abstract = result.summary.replace('\n', ' ').strip()
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."
                
                formatted_results.append(
                    f"- {result.title}\n"
                    f"  Authors: {authors}\n"
                    f"  Published: {result.published.strftime('%Y-%m-%d')}\n"
                    f"  Categories: {categories}\n"
                    f"  URL: {result.entry_id}\n"
                    f"  Abstract: {abstract}"
                )
            
            if not formatted_results:
                return f"[No arXiv papers found for query: '{query}']"
            
            return "\n\n".join(formatted_results)
            
        except ImportError:
            return "[Error: arxiv package not installed. Please install it using 'pip install arxiv']"
        except Exception as e:
            return f"[Error searching arXiv: {str(e)}]"

    @ratelimit.rate_limited(calls=30, period=60)  # 30 calls per minute
    def search_github(self, query: str, max_results: int = 3) -> str:
        """
        Search GitHub for repositories matching the query.
        Returns formatted summaries of the top results.
        """
        if not self.github_client:
            return "[Error: GitHub client not initialized. Set GITHUB_API_TOKEN environment variable for full access.]"
        
        try:
            # Search repositories
            repositories = self.github_client.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            # Format results
            formatted_results = []
            for repo in repositories[:max_results]:
                # Get additional details
                description = repo.description or "No description available"
                if len(description) > 200:
                    description = description[:197] + "..."
                
                # Format language and stats
                language = repo.language or "Not specified"
                stars = repo.stargazers_count
                forks = repo.forks_count
                
                formatted_results.append(
                    f"- {repo.full_name}\n"
                    f"  Description: {description}\n"
                    f"  Language: {language}\n"
                    f"  Stars: {stars:,}, Forks: {forks:,}\n"
                    f"  URL: {repo.html_url}"
                )
            
            if not formatted_results:
                return f"[No GitHub repositories found for query: '{query}']"
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"[Error searching GitHub: {str(e)}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_wikipedia",
                "description": "Search Wikipedia for articles matching a query. Returns formatted summaries of the top results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant Wikipedia articles."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 3).",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_arxiv",
                "description": "Search arXiv for academic papers matching a query. Returns formatted summaries including title, authors, abstract, and URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant academic papers."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 3).",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_github",
                "description": "Search GitHub for repositories matching a query. Returns formatted summaries including description, language, stars, and forks. Requires GITHUB_API_TOKEN for full access.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant GitHub repositories."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 3).",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        ] 