"""Read settings without requiring a framework or changing global environment variables."""

from dataclasses import dataclass, field
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    """Read our deliberately small KEY=value format; shell code is never executed."""
    if not path.exists():
        return {}
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip().isidentifier():
            raise ValueError(f"Invalid .env assignment on line {number}.")
        value = value.strip()
        # Matching quotes allow spaces, but interpolation would make secrets harder to reason about.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


@dataclass(frozen=True)
class Settings:
    provider: str = "openrouter"
    model: str = ""
    # repr=False prevents accidental disclosure when a beginner prints the settings object.
    openrouter_api_key: str = field(default="", repr=False)
    gemini_api_key: str = field(default="", repr=False)
    ollama_base_url: str = "http://localhost:11434"
    timeout_seconds: float = 60
    retries: int = 2
    max_tokens: int = 512
    temperature: float = 0.2
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    @classmethod
    def load(cls, env_file: Path = ROOT / ".env") -> "Settings":
        # Real environment variables win, which lets deployment settings override a local file.
        values = {**read_env(env_file), **os.environ}
        settings = cls(
            provider=values.get("LLM_PROVIDER", "openrouter").lower(),
            model=values.get("LLM_MODEL", ""),
            openrouter_api_key=values.get("OPENROUTER_API_KEY", ""),
            gemini_api_key=values.get("GEMINI_API_KEY", ""),
            ollama_base_url=values.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout_seconds=float(values.get("LLM_TIMEOUT_SECONDS", "60")),
            retries=int(values.get("LLM_RETRIES", "2")),
            max_tokens=int(values.get("LLM_MAX_TOKENS", "512")),
            temperature=float(values.get("LLM_TEMPERATURE", "0.2")),
            embedding_provider=values.get("EMBEDDING_PROVIDER", "local"),
            embedding_model=values.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        )
        if settings.timeout_seconds <= 0 or not 0 <= settings.retries <= 5:
            raise ValueError("Use a positive timeout and between 0 and 5 retries.")
        if settings.max_tokens <= 0 or not 0 <= settings.temperature <= 2:
            raise ValueError("Use positive max_tokens and temperature between 0 and 2.")
        return settings
