# Project 02: the same RAG with LangChain

**Status: scaffold only. Implementation is Step 3.**
Start with the working [shared-layer lesson](../README.md#run-your-first-request).

You will rebuild Project 01 with standard components while preserving the same
questions and documents. That gives you a fair comparison of implementation choices.

| Planned file | Learning goal |
|---|---|
| `basic_chain.py` | Prompt → model → parser, using the LCEL pipe |
| `rag_chain.py` | Retrieval and cited answers |
| `conversational_rag.py` | Rewrite follow-up questions using session history |
| `advanced_retrieval.py` | Similarity, MMR, multi-query, hybrid and re-ranking |
| `structured_output.py` | Validate answer fields with a schema |
| `streaming_and_callbacks.py` | Observe generation and usage progressively |
| `app.py` | Compare retrieval strategies in Streamlit |

| Comparison | From scratch | LangChain |
|---|---|---|
| Lines of code | Measure after implementation | Measure after implementation |
| Flexibility | Direct control of every stage | Standard interfaces with custom components |
| Debugging | Inspect your own functions | Inspect composed components and optional traces |
| Good reason to choose | Learn mechanisms or customize narrowly | Reuse integrations and composable workflows |

No install/run command is available for this application yet. Its implementation
will pin compatible current packages and consult the [official LangChain documentation](https://docs.langchain.com/oss/python/langchain/overview).
