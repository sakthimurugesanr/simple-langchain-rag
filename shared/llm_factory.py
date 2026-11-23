"""One plain-Python chat interface; provider-specific details stay in this file.

Read in this order: ModelSpec -> create_llm -> ChatClient.chat -> _request_body.
LangChain adapters, streaming and tool execution belong to later lessons.
"""

from dataclasses import dataclass, field
import json
import random
import time
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from shared.config import Settings
from shared.utils import estimate_cost

OPENROUTER = "https://openrouter.ai/api/v1"
GEMINI = "https://generativelanguage.googleapis.com/v1beta"


class ModelError(RuntimeError):
    """A safe error message; raw provider bodies might contain private user text."""


class TemporaryModelError(ModelError):
    """Only temporary failures qualify for retries or an explicitly configured fallback."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Credentials must never follow a redirect to a different server.
        return None


def request_json(method: str, url: str, headers: dict, body: dict | None, timeout: float) -> dict:
    """Keep HTTP separate so tests can replace the network with a fake function."""
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, headers={"Content-Type": "application/json", **headers}, method=method)
    try:
        with build_opener(NoRedirects()).open(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        status = error.code
        error.close()
        if status == 429 or 500 <= status < 600:
            raise TemporaryModelError(f"Provider temporarily unavailable (HTTP {status}).") from None
        raise ModelError(f"Provider rejected the request (HTTP {status}). Check key, model and permissions.") from None
    except (URLError, TimeoutError, OSError):
        raise TemporaryModelError("Cannot reach the provider. Check connectivity and timeout.") from None
    except (ValueError, UnicodeError):
        raise ModelError("Provider returned an unreadable response.") from None


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    api_key: str = field(default="", repr=False)
    base_url: str = ""
    # None means unknown; a model must be positively checked before enabling agent tools.
    supports_tools: bool | None = None
    input_price: float | None = None
    output_price: float | None = None

    def __post_init__(self):
        if self.provider not in {"openrouter", "gemini", "ollama"}:
            raise ValueError("Provider must be openrouter, gemini or ollama.")
        if not self.model.strip():
            raise ValueError("Choose a model ID from your provider's model list first.")
        if self.provider != "ollama" and not self.api_key:
            raise ValueError(f"An API key is required for {self.provider}.")
        if self.provider != "ollama" and self.base_url:
            raise ValueError("Cloud API endpoints are fixed to avoid sending keys to an arbitrary host.")
        if self.provider == "ollama":
            parsed = urlsplit(self.base_url or "http://localhost:11434")
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("Use an http(s) Ollama URL without credentials, query or fragment.")


@dataclass(frozen=True)
class ChatResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    latency_seconds: float


def list_openrouter_models(*, timeout: float = 30, request: Callable = request_json) -> list[dict]:
    """Read live capabilities and prices; a model's name alone cannot prove tool support."""
    data = request("GET", f"{OPENROUTER}/models", {}, None, timeout)
    models = []
    for item in data.get("data", []):
        pricing = item.get("pricing") or {}
        models.append({
            "id": item["id"],
            "name": item.get("name", item["id"]),
            "free": item["id"].endswith(":free"),
            "supports_tools": "tools" in (item.get("supported_parameters") or []),
            "context_length": item.get("context_length"),
            "input_price": float(pricing["prompt"]) if pricing.get("prompt") is not None else None,
            "output_price": float(pricing["completion"]) if pricing.get("completion") is not None else None,
        })
    return sorted(models, key=lambda model: model["id"])


def require_tool_support(spec: ModelSpec) -> None:
    """Later agent UIs can call this guard before building a tool-enabled graph."""
    if spec.supports_tools is not True:
        raise ValueError("Tool support is absent or unverified. Select a verified tool-capable model.")


class ChatClient:
    def __init__(self, models: list[ModelSpec], settings: Settings, *, request=request_json, sleep=time.sleep):
        if not models:
            raise ValueError("Supply at least one model.")
        self.models = models
        self.settings = settings
        self.request = request
        self.sleep = sleep

    def chat(self, messages: list[dict[str, str]]) -> ChatResult:
        """Retry temporary failures, then try only fallbacks the caller explicitly selected."""
        if not messages or not any(message.get("role") == "user" for message in messages):
            raise ValueError("Include at least one user message.")
        if any(message.get("role") not in {"system", "user", "assistant"} or not isinstance(message.get("content"), str) for message in messages):
            raise ValueError("This lesson accepts text system/user/assistant messages only.")
        started = time.monotonic()
        for spec in self.models:
            url, headers, body = self._request_body(spec, messages)
            for attempt in range(self.settings.retries + 1):
                try:
                    data = self.request("POST", url, headers, body, self.settings.timeout_seconds)
                    text, input_tokens, output_tokens = self._read_answer(spec, data)
                    return ChatResult(
                        text, spec.provider, spec.model, input_tokens, output_tokens,
                        estimate_cost(input_tokens, output_tokens, spec.input_price, spec.output_price),
                        time.monotonic() - started,
                    )
                except TemporaryModelError:
                    if attempt < self.settings.retries:
                        # Jitter avoids many clients retrying simultaneously after a busy period.
                        self.sleep(min(2 ** attempt + random.uniform(0, 0.25), 8))
        raise TemporaryModelError("All selected models are temporarily unavailable. Try again later.")

    def _request_body(self, spec, messages):
        if spec.provider == "openrouter":
            return f"{OPENROUTER}/chat/completions", {"Authorization": f"Bearer {spec.api_key}"}, {
                "model": spec.model, "messages": messages, "stream": False,
                "max_tokens": self.settings.max_tokens, "temperature": self.settings.temperature,
            }
        if spec.provider == "gemini":
            # Gemini separates system instructions and calls the assistant role 'model'.
            body = {
                "contents": [
                    {"role": "model" if item["role"] == "assistant" else "user", "parts": [{"text": item["content"]}]}
                    for item in messages if item["role"] != "system"
                ],
                "generationConfig": {"maxOutputTokens": self.settings.max_tokens, "temperature": self.settings.temperature},
            }
            instructions = [item["content"] for item in messages if item["role"] == "system"]
            if instructions:
                body["systemInstruction"] = {"parts": [{"text": "\n".join(instructions)}]}
            # A header keeps the API key out of URLs, which are often logged by HTTP servers.
            model = quote(spec.model.removeprefix("models/"), safe="")
            return f"{GEMINI}/models/{model}:generateContent", {"x-goog-api-key": spec.api_key}, body
        base_url = (spec.base_url or "http://localhost:11434").rstrip("/")
        return f"{base_url}/api/chat", {}, {
            "model": spec.model, "messages": messages, "stream": False,
            "options": {"num_predict": self.settings.max_tokens, "temperature": self.settings.temperature},
        }

    @staticmethod
    def _read_answer(spec, data):
        try:
            if data.get("error"):
                raise ModelError("Provider reported an error. Check the selected model.")
            if spec.provider == "openrouter":
                usage = data.get("usage") or {}
                text = data["choices"][0]["message"]["content"]
                counts = usage.get("prompt_tokens"), usage.get("completion_tokens")
            elif spec.provider == "gemini":
                usage = data.get("usageMetadata") or {}
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
                # Thinking tokens can also be billable; include them in this output estimate.
                output = usage.get("candidatesTokenCount")
                if output is not None:
                    output += usage.get("thoughtsTokenCount", 0)
                counts = usage.get("promptTokenCount"), output
            else:
                text = data["message"]["content"]
                counts = data.get("prompt_eval_count"), data.get("eval_count")
            if not isinstance(text, str) or not text.strip():
                raise ModelError("No answer text was returned. The provider may have blocked the response.")
            return text, *counts
        except (KeyError, IndexError, TypeError):
            raise ModelError("Provider returned no usable text. Check model availability and safety settings.") from None

    def test_connection(self) -> ChatResult:
        """A real tiny completion verifies model access; a valid key alone is insufficient."""
        return self.chat([{"role": "user", "content": "Reply with only: Connection successful"}])


def create_llm(settings: Settings | None = None, *, provider=None, model=None, api_key=None,
               model_info: dict | None = None, fallbacks: list[ModelSpec] | None = None) -> ChatClient:
    """UI overrides stay on this object; they are never written to .env or os.environ."""
    settings = settings or Settings.load()
    provider = provider or settings.provider
    model = model or settings.model
    keys = {"openrouter": settings.openrouter_api_key, "gemini": settings.gemini_api_key, "ollama": ""}
    info = model_info or {}
    if info and (provider != "openrouter" or info.get("id") != model):
        raise ValueError("Model metadata must match the selected OpenRouter model.")
    spec = ModelSpec(
        provider, model, keys.get(provider, "") if api_key is None else api_key,
        settings.ollama_base_url if provider == "ollama" else "",
        info.get("supports_tools"), info.get("input_price"), info.get("output_price"),
    )
    return ChatClient([spec, *(fallbacks or [])], settings)
