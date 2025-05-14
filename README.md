# JARVIS - AI Agent System

JARVIS is a multi-agent AI system designed to provide assistance through a conversational interface. It leverages a powerful language model via the OpenRouter API and uses a suite of specialized agents and tools to perform tasks, access knowledge, and remember information.

## Features


*   **Multi-Agent Architecture: (Ok currently is just merging the tools lol)** Core functionality is managed by an `Orchestrator` that delegates tasks to specialized agents:
    *   RAG (Retrieval Augmented Generation) Agent for knowledge base querying.
    *   Web Search Agent (powered by a local DuckDuckGo search server).
    *   File System Agent for local file operations.
    *   Computation Agent.
    *   Web API Agent.
    *   Knowledge Tools Agent (Wikipedia, ArXiv).
    *   Code Development Agent.
    *   Data Analysis Agent.
    *   System Environment Agent.
    *   Conversation Memory Agent.
    *   User Preference Agent.
*   **Tool-Using LLM:** Allows the LLM to use tools to gather information and perform actions.
*   **Long-Term Memory:**
    *   Utilizes ChromaDB as a vector store for semantic search over documents and past conversations.
    *   Indexes `.txt` files placed in the `docs/` directory for RAG.
    *   Can recall relevant past interactions and user preferences.
*   **Interactive CLI:** Chat with JARVIS directly through the command line using `agent.py`.
*   **Web API:** Exposes certain agent functionalities via a FastAPI web interface (see `main.py`), including:
    *   General agent queries.
    *   Wikipedia and ArXiv search.
    *   Memory addition and search.
    *   GitHub repository listing.
*   **Configurable:** Uses environment variables (e.g., for API keys) and a `core/config.py` file.

## Project Structure

```
.
├── agent.py            # Main CLI interaction script
├── main.py             # FastAPI web interface
├── run.sh              # Setup and execution script
├── requirements.txt    # Python dependencies
├── core/               # Core components (Orchestrator, config)
├── agents/             # Specialized agent modules
├── memory/             # Memory management (vector store, etc.)
├── tools/              # Tool definitions for agents
├── servers/            # Backend servers (e.g., search_server.py)
├── utils/              # Utility functions (if any)
├── docs/               # Place your .txt documents here for the knowledge base
├── data/               # General data storage (e.g., .gitkeep)
├── templates/          # HTML or other templates (if used by web interface)
├── vectorstore/        # Default location for ChromaDB persistence
├── c/                  # Directory for C code (if any)
├── .gitignore
└── README.md
```

## Prerequisites

*   Python 3.10+ (check requirements)

## Setup & Installation

The `run.sh` script automates most of the setup process.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kkryon/jarvis.git
    cd jarvis
    ```

2.  **API Keys:**
    *   **OpenRouter API Key (Required):** Obtain an API key from [OpenRouter.ai](https://openrouter.ai/keys).
    *   **OpenWeather API Key (Optional):** For weather functionality, get a free API key from [OpenWeatherMap](https://openweathermap.org/api).

    Set them as environment variables. You can add these to your shell's profile (e.g., `~/.bashrc` or `~/.zshrc`) or a `.env` file in the project root (ensure `.env` is in your `.gitignore`).
    ```bash
    export OPENROUTER_API_KEY='your_openrouter_key_here'
    export OPENWEATHER_API_KEY='your_openweathermap_key_here' # Optional
    ```
    If using a `.env` file, create it in the project root:
    ```
    OPENROUTER_API_KEY=your_openrouter_key_here
    OPENWEATHER_API_KEY=your_openweathermap_key_here
    ```

3.  **Make `run.sh` executable:**
    ```bash
    chmod +x run.sh
    ```

4.  **Run the setup and agent script:**
    ```bash
    ./run.sh
    ```
    This script will:
    *   Create a Python virtual environment (`venv/`).
    *   Activate it.
    *   Install dependencies from `requirements.txt`.
    *   Start the local DuckDuckGo search server (if `servers/search_server.py` exists).
    *   Launch the interactive JARVIS agent CLI (`agent.py`).

## Usage

### Interactive CLI

After running `./run.sh`, you can interact with JARVIS in your terminal. Type your queries and press Enter. Use "exit" or Ctrl+D to quit.

### Web API

The `main.py` script defines a FastAPI application. If you want to run this separately or in addition to the CLI:

1.  Ensure the virtual environment is active:
    ```bash
    source venv/bin/activate
    ```
2.  Ensure all dependencies are installed:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    The API documentation will be available at `http://127.0.0.1:8000/docs`.

### Adding to Knowledge Base

Place any `.txt` files you want JARVIS to learn from into the `docs/` directory. The system should automatically index them for retrieval when the `RAGAgent` or relevant memory functions are invoked.

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests.

## License

MIT 