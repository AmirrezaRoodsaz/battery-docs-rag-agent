"""Provider-agnostic LLM layer.

The RAG pipeline never talks to a vendor SDK directly — it calls `get_provider().complete()`.
This thin abstraction is the whole point: the model can be swapped (Gemini / Claude / OpenAI /
local Ollama) by changing one environment variable, with no change to the retrieval or
prompting code. It avoids vendor lock-in and makes the project honest about the fact that the
*RAG engineering* (grounding, citations, evaluation) is what matters, not the choice of LLM.

Each provider implements one method: `complete(system, user) -> str`. We keep generation
deterministic where the API allows (temperature 0) because for a grounded Q&A tool we want
the same answer for the same context, not creative variation.

Set the provider with LLM_PROVIDER in your .env: gemini | claude | openai | ollama.
Only the provider you actually use needs its key/SDK installed.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Raised when a provider is misconfigured (missing key/SDK) or the call fails."""


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's text completion for a system + user prompt."""


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise LLMError("GOOGLE_API_KEY is not set. Add it to .env (see .env.example).")
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise LLMError(
                "google-generativeai not installed. `pip install -r requirements.txt`"
            ) from e
        genai.configure(api_key=key)
        self._genai = genai

    def complete(self, system: str, user: str) -> str:
        model = self._genai.GenerativeModel(self.model, system_instruction=system)
        resp = model.generate_content(
            user,
            generation_config={"temperature": 0.0},
        )
        return (resp.text or "").strip()


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self) -> None:
        self.model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("ANTHROPIC_API_KEY is not set. Add it to .env (see .env.example).")
        try:
            import anthropic
        except ImportError as e:
            raise LLMError(
                "anthropic not installed. Uncomment it in requirements.txt and install."
            ) from e
        self._client = anthropic.Anthropic(api_key=key)

    def complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text").strip()


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is not set. Add it to .env (see .env.example).")
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError(
                "openai not installed. Uncomment it in requirements.txt and install."
            ) from e
        self._client = OpenAI(api_key=key)

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()


class OllamaProvider(LLMProvider):
    """Fully local provider via the Ollama HTTP API. No key, just a running `ollama serve`."""

    name = "ollama"

    def __init__(self) -> None:
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def complete(self, system: str, user: str) -> str:
        import json
        import urllib.error
        import urllib.request

        payload = json.dumps(
            {
                "model": self.model,
                "system": system,
                "prompt": user,
                "stream": False,
                "options": {"temperature": 0.0},
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate", data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read()).get("response", "").strip()
        except urllib.error.URLError as e:
            raise LLMError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running?"
            ) from e


_PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    """Instantiate the configured provider. Defaults to LLM_PROVIDER env, then gemini."""
    name = (name or os.environ.get("LLM_PROVIDER", "gemini")).lower()
    if name not in _PROVIDERS:
        raise LLMError(f"Unknown LLM_PROVIDER '{name}'. Choose one of: {', '.join(_PROVIDERS)}")
    return _PROVIDERS[name]()


def available_providers() -> list[str]:
    return list(_PROVIDERS)
