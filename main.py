from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Import the Orchestrator
from core.orchestrator import Orchestrator

# --- Global Orchestrator Instance (recommended for production) ---
# For simplicity in this example, we'll instantiate it per request,
# but for production, initialize it once when the FastAPI app starts.
# orchestrator_instance = Orchestrator()

# Initialize FastAPI app
app = FastAPI(
    title="Agent Web Interface API",
    description="API endpoints to interact with the agent's functionalities.",
    version="0.1.0"
)

# --- Pydantic Models for Request and Response Validation ---

class GeneralQueryRequest(BaseModel):
    query: str = Field(..., description="The query or command for the agent.")
    session_id: Optional[str] = Field(None, description="Optional session ID for context.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the query.")

class SearchRequest(BaseModel):
    search_term: str = Field(..., description="The term to search for.")
    max_results: int = Field(5, description="Maximum number of results to return.")

class AddMemoryRequest(BaseModel):
    text_content: str = Field(..., description="The text content to add to the agent's memory.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata associated with the memory entry.")
    document_id: Optional[str] = Field(None, description="Optional unique ID for the document.")

class SearchMemoryRequest(BaseModel):
    query_text: str = Field(..., description="The text to search for in the agent's memory.")
    top_k: int = Field(3, description="Number of top similar results to return.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for the memory search.")

class GitHubRepoRequest(BaseModel):
    username: str = Field(..., description="GitHub username or organization name.")

class AgentResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None

# --- API Endpoints ---

@app.get("/", tags=["General"])
async def root():
    return {"message": "Welcome to your Agent's Web Interface!"}

@app.post("/agent/query", response_model=AgentResponse, tags=["Agent Core"])
async def agent_general_query(request: GeneralQueryRequest):
    """
    Process a general query or command for the agent using the Orchestrator.
    """
    print(f"Received general query for Orchestrator: {request.query} (Session: {request.session_id})")
    
    try:
        # TODO: For production, use a singleton Orchestrator instance
        # orchestrator = orchestrator_instance
        orchestrator = Orchestrator() # Instantiate Orchestrator
        
        # Call the Orchestrator's chat method
        agent_response_text = orchestrator.chat(user_input=request.query)
        
        return AgentResponse(
            message="Agent processed query successfully.",
            data={"response": agent_response_text, "session_id": request.session_id}
        )
    except ImportError as e:
        # This can happen if .env is not found by dotenv, or other import issues within Orchestrator
        print(f"ERROR - ImportError during Orchestrator initialization or chat: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestrator initialization failed due to import error: {str(e)}. Check .env file and dependencies.")
    except ValueError as e:
        # This can happen if OPENROUTER_API_KEY is not set
        print(f"ERROR - ValueError during Orchestrator initialization or chat: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestrator configuration error: {str(e)}.")
    except Exception as e:
        import traceback
        print(f"ERROR - Unexpected exception during Orchestrator chat: {type(e).__name__} - {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the agent: {type(e).__name__} - {str(e)}")

@app.post("/agent/research/wikipedia", response_model=AgentResponse, tags=["Research Tools"])
async def search_wikipedia(request: SearchRequest):
    """
    Search Wikipedia for a given term.
    """
    # TODO: Implement Wikipedia API call using `wikipedia-api`
    # from your requirements.txt
    print(f"Searching Wikipedia for: {request.search_term}")
    
    # Placeholder - replace with actual Wikipedia search results
    results = [
        {"title": "Placeholder Page 1", "summary": "Summary of page 1...", "url": "http://en.wikipedia.org/wiki/Placeholder_1"},
        {"title": "Placeholder Page 2", "summary": "Summary of page 2...", "url": "http://en.wikipedia.org/wiki/Placeholder_2"}
    ]
    if not results:
        raise HTTPException(status_code=404, detail=f"No Wikipedia results found for '{request.search_term}'")
        
    return AgentResponse(
        message=f"Wikipedia results for '{request.search_term}'",
        data=results[:request.max_results]
    )

@app.post("/agent/research/arxiv", response_model=AgentResponse, tags=["Research Tools"])
async def search_arxiv(request: SearchRequest):
    """
    Search arXiv for papers matching a given term.
    """
    # TODO: Implement arXiv API call using `arxiv` library
    # from your requirements.txt
    print(f"Searching arXiv for: {request.search_term}")
    
    # Placeholder - replace with actual arXiv search results
    results = [
        {"title": "Example ArXiv Paper 1", "authors": ["Author A", "Author B"], "summary": "Abstract of paper 1..."},
        {"title": "Example ArXiv Paper 2", "authors": ["Author C"], "summary": "Abstract of paper 2..."}
    ]
    if not results:
        raise HTTPException(status_code=404, detail=f"No arXiv results found for '{request.search_term}'")

    return AgentResponse(
        message=f"ArXiv results for '{request.search_term}'",
        data=results[:request.max_results]
    )

@app.post("/agent/memory/add", response_model=AgentResponse, tags=["Agent Memory"])
async def add_to_memory(request: AddMemoryRequest):
    """
    Add information to the agent's persistent memory (e.g., ChromaDB).
    """
    # TODO: Implement logic to connect to ChromaDB (or other vector store)
    # - Create embeddings if necessary (using sentence-transformers)
    # - Add the text_content and metadata to the collection
    print(f"Adding to memory: {request.text_content[:50]}... (ID: {request.document_id})")
    
    # Placeholder
    # chroma_client = chromadb.Client() # Or however you initialize it
    # collection = chroma_client.get_or_create_collection("agent_memory")
    # collection.add(
    #     documents=[request.text_content],
    #     metadatas=[request.metadata or {}],
    #     ids=[request.document_id or str(uuid.uuid4())]
    # )
    
    return AgentResponse(
        message="Information added to memory.",
        data={"document_id": request.document_id or "auto_generated_id", "content_preview": request.text_content[:100]}
    )

@app.post("/agent/memory/search", response_model=AgentResponse, tags=["Agent Memory"])
async def search_memory(request: SearchMemoryRequest):
    """
    Search the agent's persistent memory.
    """
    # TODO: Implement logic to query ChromaDB (or other vector store)
    # - Create an embedding for request.query_text
    # - Query the collection for similar documents
    print(f"Searching memory for: {request.query_text}")

    # Placeholder
    # results = collection.query(
    #     query_texts=[request.query_text],
    #     n_results=request.top_k,
    #     where=request.filters # if filters are used
    # )

    # Placeholder response
    mock_results = [
        {"id": "doc1", "content": "Some relevant content from memory...", "score": 0.9},
        {"id": "doc2", "content": "Another piece of relevant info...", "score": 0.85}
    ]
    
    return AgentResponse(
        message=f"Memory search results for '{request.query_text}'",
        data=mock_results[:request.top_k]
    )

@app.post("/agent/tools/github/list_repos", response_model=AgentResponse, tags=["Development Tools"])
async def list_github_repos(request: GitHubRepoRequest):
    """
    List public repositories for a GitHub user or organization.
    Requires PyGithub and potentially a GitHub API token (configured via environment variables).
    """
    # TODO: Implement GitHub API call using `PyGithub`
    # from github import Github
    # g = Github("YOUR_GITHUB_TOKEN" or None) # Best to use env var for token
    # user_or_org = g.get_user(request.username) # or g.get_organization(request.username)
    # repos = user_or_org.get_repos()
    print(f"Fetching GitHub repos for: {request.username}")

    # Placeholder response
    mock_repos = [
        {"name": "repo1", "url": f"https://github.com/{request.username}/repo1", "description": "Description 1"},
        {"name": "repo2", "url": f"https://github.com/{request.username}/repo2", "description": "Description 2"}
    ]
    
    # try:
    #   actual_repos = [{"name": repo.name, "url": repo.html_url, "description": repo.description} for repo in repos]
    # except Exception as e:
    #   raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub repos: {str(e)}")

    return AgentResponse(
        message=f"GitHub repositories for '{request.username}'",
        data=mock_repos
    )

# Reminder: To run this application:
# 1. Ensure all dependencies from requirements.txt are installed: pip install -r requirements.txt
# 2. Run with Uvicorn: uvicorn main:app --reload
# 3. Access API docs at http://127.0.0.1:8000/docs 