"""Exercise UI state and model boundaries without calling a paid or external service."""

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from shared.config import Settings
from shared.llm_factory import ChatResult, TemporaryModelError

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

APP = Path(__file__).resolve().parents[1] / "app.py"


@unittest.skipIf(AppTest is None, "Install requirements.txt to test the Streamlit UI")
class UITests(unittest.TestCase):
    def setUp(self):
        # Ignore the developer's private .env file so these tests remain predictable.
        self.settings_patch = patch("shared.config.Settings.load", return_value=Settings())
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def test_offline_start_and_lesson_without_network(self):
        with patch("shared.llm_factory.create_llm") as factory:
            app = AppTest.from_file(str(APP)).run()
            self.assertFalse(app.exception)
            next(button for button in app.button if button.label == "Explain this topic").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.chat_message), 2)
            factory.assert_not_called()

    def test_live_chat_requires_configuration(self):
        app = AppTest.from_file(str(APP)).run()
        app.radio[0].set_value("Live model").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.chat_input[0].disabled)

    def test_live_chat_uses_private_key_and_shows_result(self):
        fake = Mock()
        fake.chat.return_value = ChatResult("A clear explanation.", "openrouter", "example/model", 10, 5, None, 0.2)
        with patch("shared.llm_factory.create_llm", return_value=fake) as factory:
            app = AppTest.from_file(str(APP)).run()
            app.radio[0].set_value("Live model").run()
            app.text_input(key="key_openrouter").set_value("test-key")
            app.text_input(key="model_openrouter").set_value("example/model").run()
            app.chat_input[0].set_value("What is RAG?").run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.chat_message), 2)
            self.assertEqual(factory.call_args.kwargs["api_key"], "test-key")
            self.assertNotIn("test-key", str(fake.chat.call_args))
            self.assertTrue(any(item.value == "A clear explanation." for item in app.markdown))

    def test_provider_failure_is_displayed_without_saving_incomplete_turn(self):
        fake = Mock()
        fake.chat.side_effect = TemporaryModelError("Provider temporarily unavailable.")
        with patch("shared.llm_factory.create_llm", return_value=fake):
            app = AppTest.from_file(str(APP)).run()
            app.radio[0].set_value("Live model").run()
            app.text_input(key="key_openrouter").set_value("test-key")
            app.text_input(key="model_openrouter").set_value("example/model").run()
            app.chat_input[0].set_value("Hello").run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            self.assertEqual(app.session_state["conversations"][("Live model", "openrouter", "example/model")], [])
