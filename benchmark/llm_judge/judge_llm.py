"""
judge_llm.py
------------
Thin wrapper around the existing OpenAILLM client for use in the benchmark
judge layer.  Works transparently with Ollama (OpenAI-compatible endpoint).
"""

from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.llm.openai_llm import OpenAILLM


class JudgeLLM:
    """
    Wraps OpenAILLM for benchmark judging.

    Instantiated with a model name and Ollama config dict so that
    judge calls are kept separate from generation calls.
    """

    def __init__(self, model: str, ollama_config: Dict[str, Any]):
        self._llm = OpenAILLM(
            api_key=ollama_config.get("api_key", "ollama"),
            model=model,
            api_base=ollama_config.get("api_base", "http://localhost:11434/v1"),
        )
        self._temperature = ollama_config.get("temperature", 0.1)
        self._max_tokens = ollama_config.get("max_tokens", 1024)

    def chat(self, system: str, user: str) -> str:
        messages = [
            self._llm.format_message("system", system),
            self._llm.format_message("user", user),
        ]
        return self._llm.generate(messages, temperature=self._temperature, max_tokens=self._max_tokens)
