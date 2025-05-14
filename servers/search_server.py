#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from duckduckgo_search import DDGS
import urllib.parse
import socket
import sys
import logging
import traceback
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search_server.log'),
        logging.StreamHandler()
    ]
)

class SearchHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to use our logging setup"""
        logging.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        try:
            # Parse query parameters
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            query = query_params.get('query', [''])[0]
            k = int(query_params.get('k', ['6'])[0])

            if not query:
                raise ValueError("Empty query parameter")

            logging.info(f"Processing search request: query='{query}', k={k}")

            # Perform search with timeout handling
            try:
                with DDGS() as ddg:
                    results = list(ddg.text(query, max_results=k))
            except Exception as search_error:
                logging.error(f"DuckDuckGo search failed: {str(search_error)}")
                logging.error(traceback.format_exc())
                raise RuntimeError(f"Search failed: {str(search_error)}")

            if not results:
                logging.warning(f"No results found for query: {query}")
                results = []  # Ensure empty list instead of None

            # Format results
            formatted_results = [
                {
                    'title': r.get('title', ''),
                    'url': r.get('href', ''),
                    'snippet': r.get('body', '')
                }
                for r in results
            ]

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(formatted_results).encode())
            logging.info(f"Successfully returned {len(formatted_results)} results for query: {query}")

        except ValueError as ve:
            logging.error(f"Invalid request: {str(ve)}")
            self.send_error_response(400, str(ve))
        except Exception as e:
            logging.error(f"Server error: {str(e)}")
            logging.error(traceback.format_exc())
            self.send_error_response(500, str(e))

    def send_error_response(self, code, message):
        """Helper method to send error responses"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_response = {
            'error': message,
            'timestamp': datetime.now().isoformat(),
            'status_code': code
        }
        self.wfile.write(json.dumps(error_response).encode())

def find_available_port(start_port=8823, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def run_server(start_port=8823):
    port = find_available_port(start_port)
    server_address = ('', port)
    httpd = HTTPServer(server_address, SearchHandler)
    print(f"Starting search server on port {port}...")
    
    # Write the port number to a file so the agent can read it
    with open('search_server_port.txt', 'w') as f:
        f.write(str(port))
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down search server...")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    run_server()