# The RAG learning book

This is the **Step 1 teaching chapter**, not the completed 20-chapter book. Read it
with [the repository README](../README.md) open. Full RAG, LangChain, LangGraph,
MCP, evaluation and production chapters will be added as their projects become runnable.

## Lesson 1: make one model request understandable

Imagine a very well-read student answering an exam without access to your company's
files. The student can write convincingly but may guess missing details. An LLM
has a related limitation: fluent text does not guarantee correct evidence.

An LLM predicts sequences of tokens. A token is a small piece of text, sometimes a
whole word and sometimes part of one. Providers limit the amount of input and output
that fits into one request. This capacity is called the context window.

RAG gives the model relevant passages before it answers. That resembles an open-book
exam. It improves access to evidence, but poor retrieval or unsupported reasoning
can still produce a bad answer. We will test both retrieval and answers separately.

### Why begin with the model layer?

If the network connection does not work, document search cannot fix it. First we
isolate one question and one answer. Then we add one new idea at a time. This helps
you identify which change caused a problem.

Our first experiment is runnable:

```powershell
python -m shared.connection_test --prompt "Explain a token using a simple example."
```

Use the virtual environment's Python path from the README if it is not activated.
Read the answer and the usage line. Change the question. Notice that the same code
handles different questions because the question is data passed into a function.

### Read the Python as a sentence

The runnable client is in [shared/llm_factory.py](../shared/llm_factory.py). Here is
a small reading example; the command above is the complete application:

```python
from shared.llm_factory import create_llm

# Configuration stays separate so a different provider does not change our lesson logic.
client = create_llm()
# A list preserves message order; each dictionary labels who said what.
result = client.chat([{"role": "user", "content": "What is RAG?"}])
print(result.text)
```

`client` is the object responsible for talking to the provider. `.chat(...)` asks
it to perform a task. `result.text` reads one named field of the returned answer.
The square brackets make a list; the braces make a dictionary. You will see these
same two Python structures throughout the repository.

### Why three message roles?

The system message describes the intended behaviour, the user message asks a question,
and assistant messages carry previous replies. Providers encode these roles in
different ways. Our client translates them, so the lesson code stays readable.

For example, Gemini calls an assistant message a `model` message and stores system
instructions separately. Find those translations in `_request_body()`. This is a
useful abstraction: one public interface with several internal implementations.

Temperature is a generation setting that influences sampling. Lower values can make
outputs more repeatable, but do not prove truth. A token cap limits generated output;
it does not make an excessively long input fit the context window.

### Chat and embeddings do different jobs

A chat model writes language. An embedding model places text at coordinates in a
numerical space. Later, we will search for coordinates near the question's coordinates.

Think of two maps with different coordinate systems. Numbers copied from one map
cannot automatically be used on the other. Even two embedding models with the same
vector length may assign entirely different meanings to their coordinates.

That is why [check_embedding_identity](../shared/utils.py) rejects a store created
with another embedding provider or model. In Step 2 the ingestion code will save
that identity when it creates the store. Today the guard and its offline test exist;
no vectors have been generated or stored yet.

### Reliability means handling the expected failures

A busy service may answer HTTP 429. Our client waits, then retries. The delay grows
between attempts, with a small random addition so many clients do not all retry at
once. An invalid key needs correction, so repeating it automatically is unhelpful.

Fallbacks are explicit. Passing a backup `ModelSpec` allows another selected model
to receive the same conversation after temporary failures exhaust the first model's
attempts. Review that provider choice before handling private documents.

The displayed cost estimates only the successful answer using available per-token
prices and usage. It excludes hidden failed-attempt charges, extra tools, embeddings,
taxes and other billing details. Missing prices are shown as unknown.

### How to know whether you understood this lesson

Try it yourself:

1. Run the offline tests. Explain why they do not need a real API key.
2. Find the provider's key header in `_request_body()`. Why avoid a key in a URL?
3. Set `LLM_MAX_TOKENS=64` and compare a long explanation with the default cap.
4. List OpenRouter models. Find one free ID and one model advertising tool support.
5. Explain why advertising tool support does not itself call a tool.
6. Predict the maximum attempts with two models and one retry each. Answer: four.
7. Explain why switching chat models need not require rebuilding the future vector
   store, while switching embedding models does.

## Planned full-book contents

The following chapters are a syllabus, not completed lessons:

1. LLMs, tokens, context windows and hallucinations.
2. Prompting, message roles, temperature and structured output.
3. RAG and the open-book exam analogy.
4. Loading, cleaning and chunking documents.
5. Embeddings, cosine similarity and vector databases.
6. Retrieval: top-k, thresholds, MMR, hybrid, re-ranking and query rewriting.
7. Evidence prompts, citations, missing answers and prompt injection.
8. Walking through the from-scratch project.
9. LangChain components, LCEL and the second project.
10. Tools, tool calling and agent loops.
11. LangGraph state, nodes, edges, reducers, memory, approval and streaming.
12. Agentic RAG with bounded grading and rewriting.
13. Building and consuming MCP tools and resources.
14. Choosing from-scratch code, LangChain or LangGraph.
15. Choosing models by cost, context, speed and tool support.
16. Token budgets, caching, routing and performance.
17. Evaluation and continuous improvement.
18. Production architecture, deployment, scaling and security.
19. Common mistakes and systematic debugging.
20. Further study, project ideas and glossary.

Each completed chapter will connect to real files and end with exercises. Use the
[official-reference table](../README.md#official-references-with-a-purpose) for deeper reading today.
