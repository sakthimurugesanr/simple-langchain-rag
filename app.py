"""Run with: python -m streamlit run app.py. The model logic stays in shared/.

Streamlit reruns this script on interaction. Session state preserves a conversation
in memory, while the existing factory keeps keys out of files and logs.
"""

from dataclasses import replace
from pathlib import Path

import streamlit as st

from shared.config import Settings
from shared.llm_factory import ModelError, create_llm, list_openrouter_models


LESSONS = {
    "What is RAG?": "RAG means retrieval-augmented generation. Imagine an open-book exam: first find relevant passages, then give those passages and your question to a model. The model writes an answer using that evidence. This app currently demonstrates the model connection; document retrieval is a later lesson.",
    "What is an embedding?": "An embedding represents text as a list of numbers. Similar meanings tend to have similar directions in that model's numerical space. Later we will embed both documents and questions to find related passages. Use the same embedding model for both; a chat model is a separate choice.",
    "LangChain or LangGraph?": "LangChain provides reusable components such as prompts, models and retrievers. LangGraph controls a workflow using state, nodes and edges. Start with a predictable pipeline. Add a graph when you need decisions, tool loops, memory or human approval.",
    "How does this app work?": "You choose a provider and model. The app passes your messages to create_llm(). The shared client builds the provider's request, sends it with a timeout, and converts the response into text and usage. In this offline learning mode, you are reading prewritten lessons instead of calling a model.",
}
SYSTEM_PROMPT = (
    "You are a patient AI engineering teacher. Explain ideas in plain English, "
    "use one concrete example, and explain why code is needed. Be honest about "
    "uncertainty. This is a model playground without document retrieval or tools."
)


def show_usage(usage):
    """Unknown measurements must not look like free or zero-token answers."""
    cost = usage["cost"]
    cost_text = "unknown" if cost is None else f"${cost:.8f}"
    st.caption(f"{usage['model']} · Input: {usage['input']} tokens · Output: {usage['output']} tokens · Estimated cost: {cost_text} · {usage['latency']:.2f}s")


def main():
    st.set_page_config(page_title="AI Learning Lab", page_icon="📖", layout="wide")
    try:
        saved = Settings.load()
    except (ValueError, OSError):
        # Never include malformed settings or their values in browser error messages.
        st.error("Your .env settings could not be read. Check the numeric settings and KEY=value format.")
        st.stop()

    st.markdown("""<style>
    .block-container {max-width: 1100px; padding-top: 2.5rem;}
    h1 {letter-spacing: -0.04em;}
    [data-testid="stSidebar"] {border-right: 1px solid #e3e7df;}
    [data-testid="stMetric"] {background: #f1f4ed; padding: 1rem; border-radius: 12px;}
    </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.title("📖 Learning Lab")
        st.caption("One idea. One experiment. One step forward.")
        has_config = bool(saved.model and (saved.openrouter_api_key or saved.gemini_api_key or saved.provider == "ollama"))
        mode = st.radio("Mode", ["Offline learning", "Live model"], index=1 if has_config else 0)
        st.caption("Offline lessons work immediately. Live chat uses your chosen provider.")
        providers = ["openrouter", "gemini", "ollama"]
        provider = st.selectbox("Provider", providers, index=providers.index(saved.provider) if saved.provider in providers else 0)
        key = ""
        if provider != "ollama":
            key = st.text_input("API key (optional if saved in .env)", type="password", key=f"key_{provider}")
            st.caption("Typed keys stay in this browser session and server memory; never saved to .env.")
        else:
            st.caption("Start Ollama and download a model before using live chat.")

        selected_id = None
        info = None
        if provider == "openrouter":
            if st.button("Load / refresh model list"):
                with st.spinner("Reading the public model catalogue…"):
                    try:
                        st.session_state.catalogue = list_openrouter_models(timeout=15)
                    except ModelError as error:
                        st.warning(str(error))
            catalogue = st.session_state.get("catalogue", [])
            if catalogue:
                free_only = st.checkbox("Show only :free models")
                models = [item for item in catalogue if not free_only or item["free"]]
                by_id = {item["id"]: item for item in models}
                choice = st.selectbox("Available models", ["Type a model ID", *by_id],
                                      format_func=lambda value: value if value not in by_id else f"{value} {'· FREE' if by_id[value]['free'] else ''} {'· tools ✓' if by_id[value]['supports_tools'] else ''}")
                if choice in by_id:
                    selected_id, info = choice, by_id[choice]
        if selected_id is None:
            selected_id = st.text_input("Model ID", value=saved.model if saved.provider == provider else "", key=f"model_{provider}",
                                        placeholder="Paste an exact model ID")
            if provider == "openrouter":
                info = next((item for item in st.session_state.get("catalogue", []) if item["id"] == selected_id), None)
        if info:
            st.caption(f"Tool support: {'yes' if info['supports_tools'] else 'no'} · Context: {info.get('context_length', 'unknown')}")
        elif provider == "openrouter":
            st.caption("Tool support and pricing: unverified until catalogue is loaded.")

        with st.expander("Answer settings"):
            cap = int(st.number_input("Maximum output tokens", min_value=32, max_value=8192, value=min(8192, max(32, saved.max_tokens)), step=32))
            temperature = st.slider("Temperature", 0.0, 2.0, float(saved.temperature), 0.1)
            ollama_url = st.text_input("Ollama URL", value=saved.ollama_base_url) if provider == "ollama" else saved.ollama_base_url
        settings = replace(saved, max_tokens=cap, temperature=temperature, ollama_base_url=ollama_url)

        def client():
            # A blank UI field falls back to the chosen provider's saved key.
            return create_llm(settings, provider=provider, model=selected_id.strip(), api_key=key or None, model_info=info)

        if st.button("Test connection", disabled=mode != "Live model"):
            with st.spinner("Sending a small test request…"):
                try:
                    answer = client().test_connection()
                    st.success(f"Connected to {answer.provider} / {answer.model}")
                except (ModelError, ValueError) as error:
                    st.error(str(error))
        if st.button("Clear conversation"):
            st.session_state.conversations = {}
            st.session_state.requests = {}
            st.rerun()
        st.divider()
        st.markdown("[OpenRouter keys](https://openrouter.ai/settings/keys) · [Gemini keys](https://aistudio.google.com/apikey)")

    st.caption("RAG / LESSON 01 · THE MODEL LAYER")
    st.title("Understand AI by trying it.")
    st.write("Ask a question, inspect the request, and learn what happens between a prompt and an answer.")
    a, b, c = st.columns(3)
    a.metric("Current mode", "Offline lessons" if mode == "Offline learning" else "Live chat")
    b.metric("Provider", provider.title())
    c.metric("Learning stage", "01 / Model layer")

    chat_tab, explain_tab, roadmap_tab = st.tabs(["💬 Chat", "🔎 How it works", "🧭 Learning path"])
    with explain_tab:
        st.subheader("Follow a single question")
        st.code("Your question → messages → shared model client → provider API → answer + usage", language="text")
        st.write("The provider is the service. The model is the specific AI you select. Your API key authorizes a request; it does not select a model.")
        st.write("The chat model writes answers. An embedding model will later help find relevant document passages. These are separate jobs.")
        st.info("This is the working model playground. Document upload, citations, vector search and agent tools belong to the next projects.")
        st.markdown("[Read the Python tutorial](https://docs.python.org/3/tutorial/) · [OpenRouter API](https://openrouter.ai/docs/api-reference/chat-completion) · [Gemini API](https://ai.google.dev/api/generate-content)")
    with roadmap_tab:
        st.subheader("Learn in small steps")
        for title, detail in [
            ("1. Model playground — ready", "Send messages, switch providers, inspect usage."),
            ("2. RAG from scratch — planned", "Load documents, split text, embed, retrieve and cite."),
            ("3. LangChain RAG — planned", "Rebuild the same pipeline with reusable components."),
            ("4. LangGraph and MCP — planned", "Add tools, controlled loops, memory and approval."),
        ]:
            st.markdown(f"**{title}**  \n{detail}")
        st.download_button("Download the learning README", (Path(__file__).parent / "README.md").read_text(encoding="utf-8"), file_name="RAG-README.md", mime="text/markdown")

    with chat_tab:
        # Separate histories prevent switching providers from silently forwarding another conversation.
        conversation_id = (mode, provider, selected_id)
        conversations = st.session_state.setdefault("conversations", {})
        requests = st.session_state.setdefault("requests", {})
        history = conversations.setdefault(conversation_id, [])
        question = None
        if mode == "Offline learning":
            st.info("Offline learning: these are prewritten lessons. No model, API key or network is used.")
            topic = st.selectbox("Choose a lesson", list(LESSONS))
            if st.button("Explain this topic", type="primary"):
                history.extend([{"role": "user", "content": topic}, {"role": "assistant", "content": LESSONS[topic]}])
        else:
            env_key = saved.openrouter_api_key if provider == "openrouter" else saved.gemini_api_key
            ready = bool(selected_id.strip() and (provider == "ollama" or key or env_key))
            if not ready:
                st.info("Choose a model and enter an API key in the sidebar to start live chat. You can explore offline lessons now.")
            question = st.chat_input("Ask your AI teacher a question…", disabled=not ready, max_chars=12000)

        for message in history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "usage" in message:
                    show_usage(message["usage"])

        if question:
            # Only the last four completed turns are sent to control conversation growth.
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend({"role": item["role"], "content": item["content"]} for item in history[-8:])
            messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Waiting for your model…"):
                    try:
                        answer = client().chat(messages)
                    except (ModelError, ValueError) as error:
                        # Do not save an incomplete turn: retrying should not duplicate the question.
                        st.error(str(error))
                    else:
                        usage = {"model": answer.model, "input": answer.input_tokens, "output": answer.output_tokens,
                                 "cost": answer.estimated_cost_usd, "latency": answer.latency_seconds}
                        st.markdown(answer.text)
                        show_usage(usage)
                        history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer.text, "usage": usage}])
                        requests[conversation_id] = messages
        with st.expander("Debug: messages sent to the model"):
            st.caption("Message content only. API keys and HTTP headers are never included. This app does not stream model output yet.")
            if mode == "Offline learning":
                st.write("No request is sent in offline mode.")
            else:
                if conversation_id in requests:
                    st.json(requests[conversation_id])
                else:
                    st.write("No successful model request in this conversation yet.")


if __name__ == "__main__":
    main()
