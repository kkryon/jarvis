from __future__ import annotations

import re
from typing import List, Dict, Any

from agents.base_agent import Agent


class EvaluationAgent(Agent):
    """Agent providing basic evaluation utilities for other agent responses."""

    VOWEL_PATTERN = re.compile(r"[aeiouy]+", re.I)

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = re.sub(r"[^a-z]", "", word.lower())
        if not word:
            return 0
        syllables = len(EvaluationAgent.VOWEL_PATTERN.findall(word))
        if word.endswith("e") and syllables > 1:
            syllables -= 1
        return max(1, syllables)

    @classmethod
    def _flesch_reading_ease(cls, text: str) -> float:
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        num_sentences = max(1, len(sentences))
        words = re.findall(r"[a-zA-Z]+", text)
        num_words = max(1, len(words))
        syllables = sum(cls._count_syllables(w) for w in words)
        return 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)

    def grade_readability(self, text: str) -> str:
        """Return an approximate Flesch Reading Ease score for the text."""
        score = self._flesch_reading_ease(text)
        return f"[Flesch Reading Ease: {score:.2f}]"

    def compare_responses(self, answer_a: str, answer_b: str) -> str:
        """Compare two answers and indicate which is easier to read."""
        score_a = self._flesch_reading_ease(answer_a)
        score_b = self._flesch_reading_ease(answer_b)
        if score_a == score_b:
            verdict = "A and B are equally readable"
        elif score_a > score_b:
            verdict = "A is easier to read"
        else:
            verdict = "B is easier to read"
        return (
            f"[Comparison]\nA: {score_a:.2f}\nB: {score_b:.2f}\nVerdict: {verdict}"
        )

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "grade_readability",
                "description": "Compute the Flesch Reading Ease score for a passage of text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to evaluate"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "compare_responses",
                "description": "Compare two answers and state which is more readable using Flesch score.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer_a": {"type": "string", "description": "First answer"},
                        "answer_b": {"type": "string", "description": "Second answer"}
                    },
                    "required": ["answer_a", "answer_b"]
                }
            }
        ]
