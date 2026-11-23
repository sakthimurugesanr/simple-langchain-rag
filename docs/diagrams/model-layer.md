# Step 1: follow a question through the model layer

The diagram explains currently implemented text chat, before RAG is added.

```mermaid
flowchart TD
    A[CLI question] --> B[Load settings and private key]
    B --> C[create_llm chooses ModelSpec]
    C --> D[ChatClient.chat]
    D --> E{Selected provider}
    E -->|OpenRouter| F[Chat completions JSON]
    E -->|Gemini| G[generateContent JSON]
    E -->|Ollama| H[Local chat JSON]
    F --> I[HTTP request with timeout]
    G --> I
    H --> I
    I --> J{Result}
    J -->|Success| K[Parse common ChatResult]
    J -->|Temporary error| L{Attempts left?}
    L -->|Yes| M[Wait with backoff]
    M --> I
    L -->|No| N{Explicit fallback left?}
    N -->|Yes| E
    N -->|No| O[Safe error]
    J -->|Permanent error| O
    K --> P[Text, usage, estimated cost, latency]
```

Only the selected branch runs. The default has no fallback. Catalogue metadata is
fetched separately when the CLI selects OpenRouter; it does not execute agent tools.
