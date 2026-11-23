# One-page learning cheatsheet

| Approach | Core idea | Use when |
|---|---|---|
| RAG from scratch | Load → chunk → embed → retrieve → prompt → answer | You want to understand and control each step |
| LangChain | Reusable models, prompts, parsers and retrievers | You want standard integrations and composable pipelines |
| LangGraph | State + nodes + edges + controlled loops | You need branching, tools, memory or human approval |
| MCP | Standard tool/data connection | Tools should be discoverable across compatible clients |

**Do not confuse:** chat models write; embedding models map text to numbers.
Model tool support allows tool requests; your application still validates and executes them.
RAG provides evidence; it does not guarantee correct reasoning or citations.

**Runnable now, from `RAG`:**

```powershell
python -m shared.connection_test --list-models
python -m shared.connection_test --list-models --tools-only
python -m shared.connection_test --prompt "Explain RAG in one sentence."
python -m unittest discover -s tests -v
```

Use `.\.venv\Scripts\python.exe` instead of `python` if the environment is not active.

**Before a model request:** choose provider → choose exact model → supply key →
set output cap → test connection. Never print keys.

**When a request fails:** check key/model → check HTTP status → retry temporary
errors with a limit → use only explicitly configured fallbacks.

**When RAG is implemented:** inspect chunks → inspect similarity → inspect prompt →
inspect evidence/citations → evaluate on known questions before changing models.

Start with the [README](../README.md); use the [glossary](GLOSSARY.md) for unfamiliar words.
