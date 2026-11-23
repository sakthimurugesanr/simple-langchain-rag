# Plain-English glossary

This starter glossary covers Step 1 and words you will encounter next.

| Term | Meaning |
|---|---|
| API | An agreed way for programs to ask each other for work |
| API key | A private credential identifying your account |
| Provider | The service receiving your model requests |
| Model ID | The exact name selecting a model on a provider |
| LLM | A model trained to predict and generate language |
| Token | A piece of text used to measure model input and output |
| Context window | The total input/output capacity of a model request |
| Prompt | The messages and instructions supplied to a model |
| System message | Instructions describing intended assistant behaviour |
| Temperature | A sampling setting influencing variation in generated text |
| Hallucination | A plausible generated claim without reliable factual support |
| RAG | Retrieval-augmented generation: find evidence, then answer using it |
| Chunk | A smaller passage cut from a larger document |
| Embedding | A numerical representation of text used to compare meaning |
| Vector | An ordered list of numbers |
| Cosine similarity | A comparison of vector direction; larger often means more similar |
| Vector database | A store that can search numerical representations efficiently |
| Retriever | Code selecting passages relevant to a question |
| Top-k | Return up to k search results |
| Threshold | A cutoff deciding whether a match is strong enough |
| Citation | A marker pointing from an answer to its supporting passage |
| LangChain | Components for building applications around models and tools |
| LCEL | LangChain Expression Language; `a | b` passes a result into the next component |
| Agent | A workflow in which a model can choose tools and subsequent steps |
| Tool calling | A model requesting a named operation with structured arguments |
| LangGraph | A library for controlling stateful workflows as graphs |
| State | The information carried between graph steps |
| Node / edge | A step / a connection deciding where execution goes next |
| Reducer | A rule for combining old and new state values |
| Checkpointer | A component saving workflow state for later continuation |
| Interrupt | A pause allowing external input, such as human approval |
| MCP | Model Context Protocol, a standard way to expose tools and data |
| stdio | Communication through a process's standard input and output |
| HTTP | A request/response protocol used by web APIs |
| JSON | A text format representing objects, lists, numbers and strings |
| Streaming / SSE | Delivering output progressively / one HTTP streaming format |
| Retry / backoff | Try again / wait progressively longer between tries |
| Fallback | An explicitly selected alternative after the first choice fails |
| Rate limit / HTTP 429 | A restriction on request frequency / its common HTTP status |
| Timeout | A limit on how long an operation waits |
| Latency | Elapsed time before an operation completes |
| Cache | Saved results reused to avoid repeated work |
| Prompt injection | Untrusted text trying to change an application's instructions |
| SSRF | A server being tricked into making unintended network requests |
| Environment variable | A named setting supplied to a running process |
| Virtual environment | An isolated Python package environment for one project |
| Mock | A controlled substitute for a dependency, such as a fake model response |
| Faithfulness | Whether an answer's claims are supported by the provided evidence |

Return to the [first lesson](MASTER_BOOK.md) or [README](../README.md).
