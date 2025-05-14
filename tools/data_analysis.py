import matplotlib.pyplot as plt
import json
from io import BytesIO
import base64
from jarvis.agents.base import Agent
from typing import Dict, Any

class DataAnalysisAgent(Agent):
    def plot_data(self, data_json: str, plot_type: str = "line") -> str:
        try:
            data = json.loads(data_json)
            plt.figure(figsize=(10, 6))
            
            if plot_type == "line":
                for key in data:
                    if key != "labels":
                        plt.plot(data["labels"], data[key], label=key)
                plt.legend()
            elif plot_type == "bar":
                x = range(len(data["labels"]))
                width = 0.35
                for i, key in enumerate(data):
                    if key != "labels":
                        plt.bar([x[j] + i*width for j in range(len(x))], data[key], width, label=key)
                plt.xticks([x + width/2 for x in x], data["labels"])
                plt.legend()
            elif plot_type == "scatter":
                for key in data:
                    if key != "labels":
                        plt.scatter(data["labels"], data[key], label=key)
                plt.legend()
            
            plt.tight_layout()
            
            # Save plot to base64 string
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
        except Exception as e:
            return f"[Plot generation error: {e}]"

    def analyze_text(self, text: str, analysis_type: str = "sentiment") -> str:
        # Placeholder for actual NLP implementation
        if analysis_type == "sentiment":
            # Simple sentiment analysis example
            positive_words = ["good", "great", "excellent", "positive"]
            negative_words = ["bad", "terrible", "awful", "negative"]
            
            text_lower = text.lower()
            pos_count = sum(text_lower.count(word) for word in positive_words)
            neg_count = sum(text_lower.count(word) for word in negative_words)
            
            if pos_count > neg_count:
                return "Positive sentiment detected"
            elif neg_count > pos_count:
                return "Negative sentiment detected"
            else:
                return "Neutral sentiment"
        elif analysis_type == "ner":
            return "[Named Entity Recognition not implemented]"
        elif analysis_type == "summary":
            return "[Text summarization not implemented]"
        else:
            return "[Unknown analysis type]"

    def get_tool_json_schemas(self) -> list:
        return [{
            "name": tool,
            "description": desc,
            "parameters": params
        } for tool, desc, params in [
            ("plot_data", "Generate a simple plot from JSON data", {
                "type": "object",
                "properties": {
                    "data_json": {"type": "string"},
                    "plot_type": {"type": "string", "default": "line", "enum": ["line", "bar", "scatter"]}
                },
                "required": ["data_json"]
            }),
            ("analyze_text", "Perform text analysis (sentiment, NER, summary)", {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "analysis_type": {"type": "string", "default": "sentiment", "enum": ["sentiment", "ner", "summary"]}
                },
                "required": ["text"]
            })
        ]]