# Learn RAG, LangChain and LangGraph, one working step at a time

You do not need to understand everything on this page today. Start by sending one
question to a model. Then learn how to give that model useful evidence. Finally,
learn how to let it choose tools inside a controlled workflow.

**Current milestone: Step 1 of 8 — scaffold and shared model layer.**
The provider client, command-line lab and root Streamlit model playground work now.
The three project applications, notebooks, project-specific UIs, APIs, MCP server and production features are planned;
they are not implemented yet. Folder READMEs explain what will arrive next.

## Read in this order

1. Follow [Run your first request](#run-your-first-request).
2. Read the [first teaching lesson](docs/MASTER_BOOK.md).
3. Follow [one request through the code](#follow-one-request-through-the-code).
4. Use the [glossary](docs/GLOSSARY.md) when a word is unfamiliar.
5. Keep the [cheatsheet](docs/CHEATSHEET.md) nearby while experimenting.

## Three ideas before we code

| Idea | Everyday analogy | What our code will do |
|---|---|---|
| RAG | An open-book exam | Find relevant passages before asking for an answer |
| LangChain | Reusable building blocks | Connect prompts, models, retrievers and parsers |
| LangGraph | A flowchart with memory | Decide which step runs next, including retries and tools |

A **provider** is the service receiving your request. A **model** is the particular
AI you choose on that service. OpenRouter is a provider, not a single model.
An **embedding model** turns text into numbers for searching; it is a separate choice
from the chat model that writes an answer.

## What exists today

```text
RAG/
  README.md
  .env.example                  # safe configuration template
  app.py                        # working Streamlit model playground
  requirements.txt              # pinned Streamlit dependency for the UI
  shared/
    config.py                   # settings and private key loading
    llm_factory.py              # OpenRouter, Gemini and Ollama text chat
    connection_test.py          # runnable command-line lab
    utils.py                    # cost, hashing and embedding identity helpers
  tests/test_shared.py          # offline tests, no key required
  docs/
    MASTER_BOOK.md              # Step 1 lesson; full 20-chapter book comes in Step 8
    GLOSSARY.md
    CHEATSHEET.md
    diagrams/model-layer.md
  01-rag-from-scratch/           # Step 2 scaffold
  02-langchain-rag/              # Step 3 scaffold
  03-langgraph-agent/            # Steps 4–5 scaffold
```

## Run your first request

Use **Python 3.11 or newer**, preferably Python 3.12. In PowerShell, first move
into the `RAG` folder inside this repository. All commands below run from there.

```powershell
Set-Location '.\RAG'
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The virtual environment is a private package workspace for these lessons. Calling
its Python executable directly avoids PowerShell activation-policy problems.
The command-line client uses only built-in Python modules. The web UI uses pinned
Streamlit. Dependencies for the later projects will accompany their implementation.

### Start the web UI

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open [the local app](http://127.0.0.1:8502). The **Offline learning** mode works
without a key and clearly labels its prewritten lessons. Choose **Live model** for
real model chat: select a provider, load OpenRouter's model list or type an exact
model ID, and enter your key privately in the sidebar. Existing `.env` keys are used
when the key field is blank. Typed keys stay in session memory and are not saved.

The UI includes connection testing, recent conversation history, output settings,
usage/cost, an exact successful-request debug view and a learning path. Answers
appear when generation completes; token streaming and document retrieval come later.
The server binds to your computer only. To stop it, press Ctrl+C in its terminal.

If `python` cannot run or opens the Microsoft Store, install Python from the
[official Python downloads page](https://www.python.org/downloads/windows/), reopen
PowerShell, and try `py -3.12 --version`. You can substitute `py -3.12` for `python`
when creating the environment. Do not proceed until the version command works.

Choose **one** provider below. A request can incur charges according to your
provider account and model. Listing OpenRouter models does not make a chat request.

### Option A: OpenRouter

1. Create a key at [OpenRouter keys](https://openrouter.ai/settings/keys).
2. Discover current model IDs:

   ```powershell
   .\.venv\Scripts\python.exe -m shared.connection_test --list-models
   .\.venv\Scripts\python.exe -m shared.connection_test --list-models --tools-only
   ```

3. Open `.env` in your editor and fill in:

   ```dotenv
   LLM_PROVIDER=openrouter
   LLM_MODEL=PASTE_AN_EXACT_MODEL_ID_FROM_THE_LIST
   OPENROUTER_API_KEY=PASTE_YOUR_PRIVATE_KEY
   ```

4. Send a short question:

   ```powershell
   .\.venv\Scripts\python.exe -m shared.connection_test
   ```

**Observe:** an explanation of RAG, provider/model, input/output tokens, estimated
answer cost, and elapsed time. Wording varies. Unknown price or missing token usage
is displayed as unknown, rather than incorrectly called free.
`:free` IDs are labelled in the catalogue; availability, quotas and tool support can change.

### Option B: Gemini

Get a key from [Google AI Studio](https://aistudio.google.com/apikey). Choose an
available text-generation model from [Google's model documentation](https://ai.google.dev/gemini-api/docs/models).
Set `LLM_PROVIDER=gemini`, `LLM_MODEL` to its exact ID, and `GEMINI_API_KEY` in `.env`.
Run the same connection-test command. Gemini prices are unknown by default in this
lesson because its tiers and billing options require separate pricing configuration.

### Option C: Ollama on your computer

Install [Ollama](https://ollama.com/download), choose a model that fits your hardware
from its [model library](https://ollama.com/library), and run `ollama pull YOUR_MODEL_ID`.
Keep Ollama running. Set `LLM_PROVIDER=ollama`, `LLM_MODEL` to that installed model,
and `OLLAMA_BASE_URL=http://localhost:11434`. Then run the same connection test.
No cloud key is needed. Local hardware and electricity still have costs; this lab
does not estimate them. A remote Ollama URL must be a server you trust.

### Verify without any key or network

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Observe:** the offline tests pass using fake provider responses. These tests verify
request formats, safe failures, retry limits, fallback, metadata, cost and settings.
They do not verify your account, current model availability or actual answer quality.

## Follow one request through the code

Read [connection_test.py](shared/connection_test.py) first. It is the smallest complete
application. Then open [llm_factory.py](shared/llm_factory.py).

1. `Settings.load()` reads `.env` and environment variables. Real environment values win.
2. `create_llm()` chooses a provider, model and private key. It returns a `ChatClient`.
3. `chat()` receives messages such as `{"role": "user", "content": "What is RAG?"}`.
4. `_request_body()` translates those messages into the chosen provider's HTTP format.
5. `request_json()` sends JSON with a timeout. It hides raw response errors and rejects redirects.
6. `_read_answer()` turns different provider responses into the same `ChatResult`.

`ChatResult` is a small labelled box containing answer text, model, usage, cost and time.
This common result means later applications can switch providers without duplicating
their document-search logic. See the [request flow diagram](docs/diagrams/model-layer.md).

### Retry and fallback, explained simply

A retry asks the same model again after a temporary failure. A fallback asks another
model you explicitly configured. HTTP 429 and 5xx errors and connectivity failures
qualify here. Invalid keys, invalid requests and blocked/empty answers do not.
With two retries and two configured models there are at most six HTTP attempts.
Retries may repeat a request that the provider already processed; usage can exceed
the successful answer's displayed estimate.

The default has **no fallback**. This avoids silently sending data to another provider.
To opt in from Python, pass a list of `ModelSpec` objects to `create_llm(fallbacks=...)`.
Each spec names its provider, exact model and key. The order is the fallback order.

## What Step 1 does and what comes later

| Feature | Status |
|---|---|
| OpenRouter / Gemini / Ollama text completion | Implemented |
| Live OpenRouter catalogue, `:free` label, tool metadata | Implemented as functions and CLI |
| Memory-only key/model overrides | Implemented in `create_llm()` |
| Connection test, bounded retry, explicit fallback | Implemented |
| Token usage and per-answer cost estimate | Implemented; unknown when metadata is missing |
| Separate embedding settings and identity guard | Implemented; vector-store metadata writing comes in Step 2 |
| Embedding generation, chunking, vector search | Step 2 |
| Streamlit model playground and provider/model sidebar | Implemented in root `app.py` |
| Token streaming and document RAG interfaces | Step 2 |
| LangChain adapters and retrieval strategies | Step 3 |
| Agent tool execution, LangGraph, approval and memory | Step 4 |
| MCP server and integration | Step 5 |
| FastAPI, caching, Docker and deployment | Step 6 |
| Full project pytest/evaluation suites | Step 7 |
| Full 20-chapter master book | Step 8; first lesson available now |

Step 1 handles text chat only. Tool capability metadata does not execute tools.
The root `app.py` runs the model playground. The three project-specific apps remain planned.

## Start here: Day 1 to Day 7

This is the intended learning path for the completed repository. Only Day 1 is
currently executable; the other entries name the exact files to be built next.

| Day | Run or read | What you should learn | Availability |
|---|---|---|---|
| 1 | `python -m shared.connection_test`; `shared/config.py`; `shared/llm_factory.py` | Send one question; distinguish provider, model, tokens and embeddings | Ready |
| 2 | `01-rag-from-scratch/notebooks/01_chunking_visualized.ipynb`; `02_embeddings_and_cosine.ipynb` in the same folder | Split text and compare meaning numerically | Planned |
| 3 | `01-rag-from-scratch/notebooks/03_retrieval_and_prompt.ipynb`; `04_full_pipeline.ipynb`; `01-rag-from-scratch/app.py` | Retrieve evidence, inspect prompts and cite sources | Planned |
| 4 | `02-langchain-rag/basic_chain.py`; `rag_chain.py`; `conversational_rag.py` in that project | Rebuild the same pipeline with LCEL and history | Planned |
| 5 | `02-langchain-rag/advanced_retrieval.py`; `structured_output.py`; `streaming_and_callbacks.py`; `app.py` | Compare retrieval and inspect structured/streaming answers | Planned |
| 6 | `03-langgraph-agent/examples/01_hello_graph.py` through `07_agentic_rag.py` | Learn state, tools, memory, approval and bounded re-evaluation | Planned |
| 7 | `03-langgraph-agent/examples/08_mcp_integration.py`; `mcp_server/server.py`; `app.py` in that project | Connect MCP tools; then read deployment and evaluation lessons | Planned |

Future UIs will run from `RAG` with `python -m streamlit run PROJECT/app.py` after
installing that project's requirements. Those commands are **for later milestones**.

## Official references, with a purpose

| Link | Why read it |
|---|---|
| [Python tutorial](https://docs.python.org/3/tutorial/) | Functions, dictionaries, classes and exceptions |
| [Python virtual environments](https://docs.python.org/3/library/venv.html) | Understand the isolated environment you created |
| [OpenRouter models endpoint](https://openrouter.ai/docs/api-reference/models/get-models) | Model IDs, supported parameters and prices |
| [OpenRouter chat API](https://openrouter.ai/docs/api-reference/chat-completion) | Compare our JSON request with the provider contract |
| [Gemini generateContent API](https://ai.google.dev/api/generate-content) | Contents, system instructions and usage metadata |
| [Ollama chat API](https://docs.ollama.com/api/chat) | Local chat requests and usage counts |
| [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview) | Preview the reusable components in Project 02 |
| [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) | Preview controlled workflows in Project 03 |
| [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro) | Understand the standard connection for tools and data |

Provider contracts were checked on **27 October 2026**. We intentionally avoid a
hard-coded "best free model": the live catalogue is the right place to choose one.

## Troubleshooting

| Symptom | First action |
|---|---|
| `No module named shared` | Run the command from inside `RAG`, with `-m shared.connection_test` |
| Missing model/key error | Fill in `.env`; leave no placeholder model ID |
| HTTP 401/403 | Check the key, selected account, model permissions and billing |
| HTTP 400/404 | Check the exact model ID and supported request settings |
| HTTP 429 | Wait or explicitly configure an available fallback; free models have quotas |
| All models unavailable | Check network access, provider status or whether Ollama is running |
| Cost is `unknown` | Price metadata or usage is missing; this is not a zero-cost claim |
| Changed embedding model | Re-index into a new store when Step 2 is implemented |

Never commit `.env` or paste a private key into a screenshot. The small `.env`
reader accepts one `KEY=value` per line, optional matching quotes and whole-line
comments. It deliberately does not support shell execution, variable interpolation,
multiline values or inline comments; put comments on separate lines.
