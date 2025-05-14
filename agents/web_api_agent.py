from __future__ import annotations

import os
import json
import requests
from typing import List, Dict, Any

from agents.base_agent import Agent

# ────────────────────────────────────────────────────────────────────────
# 2D. WEB & API AGENT
# ────────────────────────────────────────────────────────────────────────
class WebAPIAgent(Agent):
    """Agent for fetching URLs and interacting with web APIs like weather."""
    def fetch_url(self, url: str) -> str:
        """Fetch the raw text content of a given URL."""
        print(f"WebAPIAgent: Fetching URL: {url}")
        try:
            # Add a user-agent to be polite
            headers = {'User-Agent': 'JARVIS-AI-Agent/1.0'}
            resp = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            resp.raise_for_status()
            # Basic content type check, could be expanded
            if 'text/html' in resp.headers.get('Content-Type', '') or '<html' in resp.text[:1000].lower():
                 # For HTML, it might be better to use a dedicated HTML parser/agent
                 # or summarize. For now, return a snippet or a warning.
                 # Let's try to return a summary or an indication it's HTML.
                 # This is a placeholder for more sophisticated HTML handling.
                 # from bs4 import BeautifulSoup # Example if you add BeautifulSoup
                 # soup = BeautifulSoup(resp.text, 'html.parser')
                 # return f"[HTML Content Retrieved from {url}. Title: {soup.title.string if soup.title else 'N/A'}. Snippet: {soup.get_text()[:500]}...]"
                 return f"[HTML content from {url}. Consider using a specialized HTML parser or summarizer if needed. First 500 chars: {resp.text[:500]}...]"

            return resp.text[:8000] # Limit response size
        except requests.exceptions.RequestException as e:
            return f"[Error fetching URL '{url}': {e}]"

    def weather(self, location: str) -> str:
        """Get current weather for a location using OpenWeatherMap API."""
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return "[Error: OPENWEATHER_API_KEY environment variable not set. Cannot fetch weather.]"
        
        print(f"WebAPIAgent: Getting weather for '{location}'")
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {'q': location, 'appid': api_key, 'units': 'metric'}
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            main_data = data.get('main', {})
            weather_data = data.get('weather', [{}])[0]
            wind_data = data.get('wind', {})

            temp = main_data.get('temp', 'N/A')
            feels_like = main_data.get('feels_like', 'N/A')
            humidity = main_data.get('humidity', 'N/A')
            description = weather_data.get('description', 'N/A')
            wind_speed = wind_data.get('speed', 'N/A')
            city_name = data.get('name', location)

            return (
                f"Current weather in {city_name}:\\n"
                f"  Temperature: {temp}°C (feels like {feels_like}°C)\\n"
                f"  Conditions: {description}\\n"
                f"  Humidity: {humidity}%\\n"
                f"  Wind Speed: {wind_speed} m/s"
            )
        except requests.exceptions.RequestException as e:
            return f"[Error fetching weather data for '{location}': {str(e)}]"
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"[Error parsing weather data for '{location}': {str(e)}]"

    # translate placeholder
    def translate(self, text: str, target_lang: str = "en") -> str:
        return f"[Translation API (e.g., Google Translate) not implemented. Request: '{text}' -> {target_lang}]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fetch_url",
                "description": "Fetch the raw text content of a given URL. Returns up to 8000 characters. For HTML, it may return a snippet and a warning.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to fetch (e.g., \"http://example.com\")."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "weather",
                "description": "Get current weather information for a specified location using OpenWeatherMap API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and optionally country (e.g., \"London,UK\", \"Paris\")."}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "translate",
                "description": "Translate text to another language (placeholder).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to translate."},
                        "target_lang": {"type": "string", "description": "The target language code (e.g., 'es', 'fr', 'de'). Defaults to 'en'.", "default": "en"}
                    },
                    "required": ["text"]
                }
            }
        ]