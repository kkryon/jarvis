import requests
import os
import json

class WebAPIAgent:
    def fetch_url(self, url):
        try:
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'JARVIS-AI-Agent/1.0'})
            resp.raise_for_status()
            return resp.text[:8000]
        except Exception as e:
            return f"[Error: {e}]"

    def weather(self, location):
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return "[Error: OPENWEATHER_API_KEY not set]"
        try:
            resp = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return f"Current weather in {data['name']}:\n  Temperature: {data['main']['temp']}°C\n  Conditions: {data['weather'][0]['description']}\n  Humidity: {data['main']['humidity']}%\n  Wind Speed: {data['wind']['speed']} m/s"
        except Exception as e:
            return f"[Error: {e}]"