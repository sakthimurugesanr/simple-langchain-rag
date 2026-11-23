"""Offline contract tests exercise failure paths without spending tokens or exposing keys."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from shared.config import Settings, read_env
from shared.llm_factory import (
    ChatClient, ModelError, ModelSpec, TemporaryModelError,
    create_llm, list_openrouter_models, request_json, require_tool_support,
)
from shared.utils import check_embedding_identity, estimate_cost


def openrouter_answer():
    # A tiny provider-shaped response verifies parsing rather than the real service.
    return {"choices": [{"message": {"content": "Hello"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2}}


class SharedTests(unittest.TestCase):
    def test_provider_payloads_and_usage(self):
        cases = [
            ("openrouter", openrouter_answer(), (10, 2)),
            ("gemini", {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}],
                        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 2,
                                          "thoughtsTokenCount": 3}}, (10, 5)),
            ("ollama", {"message": {"content": "Hello"}, "prompt_eval_count": 10, "eval_count": 2}, (10, 2)),
        ]
        for provider, response, expected in cases:
            with self.subTest(provider=provider):
                calls = []
                def fake(method, url, headers, body, timeout):
                    calls.append((url, headers, body))
                    return response
                spec = ModelSpec(provider, "test-model", "private-key")
                client = ChatClient([spec], Settings(), request=fake)
                result = client.chat([{"role": "system", "content": "Teach simply"},
                                      {"role": "user", "content": "Hello"}])
                self.assertEqual(result.text, "Hello")
                self.assertEqual((result.input_tokens, result.output_tokens), expected)
                url, headers, body = calls[0]
                self.assertNotIn("private-key", url)
                if provider == "gemini":
                    self.assertEqual(body["systemInstruction"]["parts"][0]["text"], "Teach simply")
                    self.assertEqual(len(body["contents"]), 1)
                    self.assertEqual(headers["x-goog-api-key"], "private-key")
                if provider == "ollama":
                    self.assertFalse(body["stream"])
                    self.assertEqual(body["options"]["num_predict"], 512)

    def test_retry_then_fallback_is_bounded(self):
        seen, waits = [], []
        def fake(method, url, headers, body, timeout):
            seen.append(body["model"])
            if body["model"] == "primary":
                raise TemporaryModelError("busy")
            return openrouter_answer()
        specs = [ModelSpec("openrouter", name, "secret") for name in ["primary", "backup"]]
        result = ChatClient(specs, Settings(retries=1), request=fake, sleep=waits.append).test_connection()
        self.assertEqual(seen, ["primary", "primary", "backup"])
        self.assertEqual(len(waits), 1)
        self.assertEqual(result.model, "backup")

    def test_permanent_failure_does_not_retry_or_fallback(self):
        calls = []
        def fake(*args):
            calls.append(args)
            raise ModelError("HTTP 401")
        specs = [ModelSpec("openrouter", name, "secret") for name in ["primary", "backup"]]
        with self.assertRaises(ModelError):
            ChatClient(specs, Settings(), request=fake).test_connection()
        self.assertEqual(len(calls), 1)

    def test_http_error_classification_and_redaction(self):
        for code, expected in [(401, ModelError), (429, TemporaryModelError), (503, TemporaryModelError)]:
            with self.subTest(code=code):
                with patch("shared.llm_factory.build_opener") as opener:
                    opener.return_value.open.side_effect = HTTPError("https://example.test", code, "SECRET", {}, None)
                    with self.assertRaises(expected) as caught:
                        request_json("GET", "https://example.test", {}, None, 1)
                    self.assertNotIn("SECRET", str(caught.exception))

    def test_live_metadata_controls_tool_guard_and_cost(self):
        def fake(*args):
            return {"data": [{"id": "example/model:free", "supported_parameters": ["tools"],
                              "pricing": {"prompt": "0", "completion": "0"}}]}
        item = list_openrouter_models(request=fake)[0]
        self.assertTrue(item["free"])
        client = create_llm(Settings(openrouter_api_key="secret"), model=item["id"], model_info=item)
        require_tool_support(client.models[0])
        self.assertEqual(client.models[0].input_price, 0)
        with self.assertRaises(ValueError):
            require_tool_support(ModelSpec("ollama", "unverified"))

    def test_unrelated_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            create_llm(Settings(openrouter_api_key="secret"), model="one", model_info={"id": "two"})

    def test_unknown_cost_is_not_reported_as_free(self):
        self.assertIsNone(estimate_cost(10, 2))
        self.assertEqual(estimate_cost(10, 2, 0, 0), 0)
        self.assertAlmostEqual(estimate_cost(10, 2, 0.001, 0.002), 0.014)

    def test_settings_and_spec_hide_keys(self):
        settings = Settings(openrouter_api_key="secret", gemini_api_key="another-secret")
        self.assertNotIn("secret", repr(settings))
        self.assertNotIn("secret", repr(ModelSpec("openrouter", "model", "secret")))

    def test_ui_override_does_not_change_settings(self):
        settings = Settings(openrouter_api_key="saved-key", model="model")
        client = create_llm(settings, api_key="memory-only")
        self.assertEqual(settings.openrouter_api_key, "saved-key")
        self.assertEqual(client.models[0].api_key, "memory-only")

    def test_embedding_mismatch_is_blocked(self):
        # Keep fixtures inside the workspace so restricted Windows runners can write them.
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "metadata.json"
            path.write_text('{"embedding_provider": "local", "embedding_model": "model-a"}')
            check_embedding_identity(path, "local", "model-a")
            with self.assertRaises(ValueError):
                check_embedding_identity(path, "local", "model-b")

    def test_env_subset_and_environment_precedence(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / ".env"
            path.write_text('# A comment explains why this setting exists.\nLLM_MODEL="file-model"\n', encoding="utf-8")
            self.assertEqual(read_env(path)["LLM_MODEL"], "file-model")
            with patch.dict("os.environ", {"LLM_MODEL": "deployment-model"}):
                self.assertEqual(Settings.load(path).model, "deployment-model")

    def test_empty_or_blocked_answer_is_clear(self):
        client = ChatClient([ModelSpec("gemini", "model", "secret")], Settings(), request=lambda *args: {})
        with self.assertRaises(ModelError):
            client.test_connection()


if __name__ == "__main__":
    unittest.main()
