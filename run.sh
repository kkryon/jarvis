#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up JARVIS AI Agent...${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to the script's directory (project root)
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Check for OpenWeather API key
if [ -z "$OPENWEATHER_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENWEATHER_API_KEY environment variable is not set${NC}"
    echo -e "${BLUE}To enable weather functionality, set your OpenWeather API key:${NC}"
    echo -e "export OPENWEATHER_API_KEY='your_api_key_here'"
    echo -e "You can get a free API key at: https://openweathermap.org/api\n${NC}"
fi

# Check for OpenRouter API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}Critical: OPENROUTER_API_KEY environment variable is not set${NC}"
    echo -e "${BLUE}The agent requires this key to function with the OpenRouter API.${NC}"
    echo -e "Set it by running: export OPENROUTER_API_KEY='your_openrouter_key_here'"
    echo -e "You can get an API key from: https://openrouter.ai/keys\n${NC}"
    # Optionally exit if the key is critical for startup
    # exit 1
fi

# Create necessary directories
echo -e "${BLUE}Creating necessary directories (docs, vectorstore, tools)...${NC}"
mkdir -p "${SCRIPT_DIR}/docs"
mkdir -p "${SCRIPT_DIR}/vectorstore"
mkdir -p "${SCRIPT_DIR}/tools" # If your agent still uses a local tools directory structure

# Create virtual environment if it doesn't exist
if [ ! -d "${SCRIPT_DIR}/venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv "${SCRIPT_DIR}/venv"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "${SCRIPT_DIR}/venv/bin/activate"

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing dependencies from requirements.txt...${NC}"
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    # First try installing everything
    if ! python -m pip install -r "${SCRIPT_DIR}/requirements.txt"; then
        echo -e "${YELLOW}Warning: Some dependencies may have failed to install with the primary method. Attempting to install core packages and handle re2 separately...${NC}"
        # Install core packages (adjust list as necessary)
        python -m pip install requests python-dotenv chromadb sentence-transformers wikipedia-api arxiv PyGithub ratelimit openai duckduckgo-search jsonschema paho-mqtt opcua pymodbus pydantic

        # Try installing re2 separately and make it optional
        echo -e "${BLUE}Attempting to install re2 (optional)...${NC}"
        if ! python -m pip install re2; then
            echo -e "${YELLOW}Warning: Failed to install re2 package. This is optional and the agent will continue to function.${NC}"
            echo -e "${BLUE}If you need re2 functionality, consider using Python 3.11 or earlier.${NC}"
        fi
    fi
else
    echo -e "${RED}Error: requirements.txt not found in ${SCRIPT_DIR}. Please create it.${NC}"
fi


# Verify critical dependencies and CUDA availability
echo -e "${BLUE}Verifying dependencies and CUDA availability...${NC}"
# Updated to check for openai instead of transformers
# Note: torch is a dependency of sentence-transformers typically.
COMMAND_TO_RUN="import torch; import openai; import duckduckgo_search; print('Dependencies verified successfully!'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device count: {torch.cuda.device_count()}'); print(f'Current CUDA device: {torch.cuda.current_device()}')"
if ! python -c "${COMMAND_TO_RUN}" 2>/dev/null; then
    echo -e "${RED}Error: Some dependencies are missing or CUDA check failed. Attempting to install some core packages...${NC}"
    # Updated to install openai instead of transformers
    python -m pip install openai duckduckgo-search chromadb sentence-transformers requests
    echo -e "${BLUE}Please re-run the script. If issues persist, check PyTorch/CUDA installation manually if sentence-transformers require GPU.${NC}"
fi

# Clean up any existing port file
rm -f "${SCRIPT_DIR}/search_server_port.txt"

SEARCH_SERVER_PID=""
# Start the search server in the background
# Check if search_server.py exists before trying to run it
if [ -f "${SCRIPT_DIR}/servers/search_server.py" ]; then
    echo -e "${BLUE}Starting DuckDuckGo web search server...${NC}"
    # Ensure the servers directory exists (it should, but good to be safe)
    mkdir -p "${SCRIPT_DIR}/servers"
    # Ensure server is executable or run with python
    python3 -u "${SCRIPT_DIR}/servers/search_server.py" &
    SEARCH_SERVER_PID=$!

    # Wait a moment for the server to start and create the port file
    echo -e "${BLUE}Waiting for search server to initialize...${NC}"
    sleep 3 # Increased sleep time slightly

    # Check if the search server started successfully
    if ! kill -0 $SEARCH_SERVER_PID 2>/dev/null; then
        echo -e "${RED}Error: Web search server failed to start${NC}"
        SEARCH_SERVER_PID=""
        # Decide if this is fatal or just a warning
        # exit 1 # Uncomment to make it fatal
    else
        # Wait for the port file to be created
        timeout=15 # Increased timeout
        echo -e "${BLUE}Waiting for search_server_port.txt...${NC}"
        while [ ! -f "${SCRIPT_DIR}/search_server_port.txt" ] && [ $timeout -gt 0 ]; do
            sleep 1
            timeout=$((timeout - 1))
        done

        if [ ! -f "${SCRIPT_DIR}/search_server_port.txt" ]; then
            echo -e "${RED}Error: Search server port file not created after timeout. Web search might not work.${NC}"
            echo -e "${BLUE}Attempting to stop potentially misbehaving search server (PID: $SEARCH_SERVER_PID)...${NC}"
            kill $SEARCH_SERVER_PID 2>/dev/null
            SEARCH_SERVER_PID=""
        else
            echo -e "${GREEN}Web search server started successfully on port $(cat "${SCRIPT_DIR}/search_server_port.txt")${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Warning: ${SCRIPT_DIR}/servers/search_server.py not found. Web search functionality will be unavailable.${NC}"
fi


# Run the agent
echo -e "${GREEN}Starting JARVIS AI Agent Main Application...${NC}"
python3 -u "${SCRIPT_DIR}/agent.py"

# Cleanup: kill the search server when the agent exits
if [ ! -z "$SEARCH_SERVER_PID" ] && kill -0 $SEARCH_SERVER_PID 2>/dev/null; then
    echo -e "${BLUE}Stopping web search server (PID: $SEARCH_SERVER_PID)...${NC}"
    kill $SEARCH_SERVER_PID
    rm -f "${SCRIPT_DIR}/search_server_port.txt"
    echo -e "${GREEN}Web search server stopped.${NC}"
fi

# Deactivate virtual environment
echo -e "${BLUE}Deactivating virtual environment...${NC}"
deactivate

echo -e "${GREEN}JARVIS AI Agent script finished.${NC}" 