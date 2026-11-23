"""A small command-line lab lets you verify the shared layer before building a UI."""

import argparse

from shared.config import Settings
from shared.llm_factory import ModelError, create_llm, list_openrouter_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-models", action="store_true", help="List live OpenRouter models; no key required")
    parser.add_argument("--tools-only", action="store_true", help="Filter that list to tool-capable models")
    parser.add_argument("--provider", choices=["openrouter", "gemini", "ollama"])
    parser.add_argument("--model", help="Use an exact model ID from the provider")
    parser.add_argument("--prompt", default="Explain RAG in two sentences for a beginner.")
    args = parser.parse_args()
    try:
        if args.list_models:
            for item in list_openrouter_models():
                if args.tools_only and not item["supports_tools"]:
                    continue
                print(f"{item['id']} | {'FREE' if item['free'] else 'check pricing'} | tools={item['supports_tools']}")
            return
        settings = Settings.load()
        provider = args.provider or settings.provider
        model = args.model or settings.model
        info = None
        if provider == "openrouter":
            try:
                info = next((item for item in list_openrouter_models() if item["id"] == model), None)
            except ModelError:
                # Metadata failure need not prevent an ordinary chat; cost stays unknown.
                print("Model catalogue unavailable. Tool capability and price are unverified.")
        client = create_llm(settings, provider=provider, model=model, model_info=info)
        result = client.chat([{"role": "user", "content": args.prompt}])
        print(result.text)
        print(f"\nProvider: {result.provider} | Model: {result.model}")
        print(f"Tokens: input={result.input_tokens}, output={result.output_tokens}")
        cost = "unknown" if result.estimated_cost_usd is None else f"${result.estimated_cost_usd:.8f}"
        print(f"Estimated answer cost: {cost} | Time including retries: {result.latency_seconds:.2f}s")
    except (ModelError, ValueError) as error:
        # These are deliberately redacted messages; never print a raw HTTP response or key.
        parser.exit(1, f"Setup/connection error: {error}\n")


if __name__ == "__main__":
    main()
