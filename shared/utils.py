"""Small pure helpers are easy to understand and test without an API key."""

import hashlib
import json
from pathlib import Path


def content_hash(text: str) -> str:
    """The same content gets the same fingerprint, enabling deduplication later."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_embedding_identity(metadata_path: Path, provider: str, model: str) -> None:
    """Check an existing store before using it; this does not create a vector store."""
    if not metadata_path.exists():
        return
    saved = json.loads(metadata_path.read_text(encoding="utf-8"))
    if saved.get("embedding_provider") != provider or saved.get("embedding_model") != model:
        # Equal vector lengths do not imply equal meaning: different models use different coordinates.
        raise ValueError("Embedding model changed. Re-index documents in a new vector store.")


def estimate_cost(input_tokens, output_tokens, input_price=None, output_price=None):
    """Prices are USD per TOKEN, as returned by OpenRouter; unknown is not free."""
    if any(value is None for value in (input_tokens, output_tokens, input_price, output_price)):
        return None
    return input_tokens * input_price + output_tokens * output_price
