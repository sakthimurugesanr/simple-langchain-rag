# Project 01: RAG from scratch

**Status: scaffold only. Implementation is Step 2.**
Start with the working [shared-layer lesson](../README.md#run-your-first-request).

You will build one function at a time: load a file, clean text, split it into chunks,
embed the chunks, store vectors, embed a question, retrieve passages, build a prompt,
and generate a cited answer. No LangChain will hide these steps.

The planned Streamlit UI will let you upload documents, add safe URLs, delete sources,
chat with streaming, inspect scores and read the exact prompt. It is not runnable yet.

Planned notebooks in `notebooks/`, in order:

1. `01_chunking_visualized.ipynb` — compare chunk boundaries.
2. `02_embeddings_and_cosine.ipynb` — see similarity numerically and in a 2D projection.
3. `03_retrieval_and_prompt.ipynb` — connect evidence to a question.
4. `04_full_pipeline.ipynb` — combine the complete pipeline.

The next milestone will add exact install/run commands and examples of expected output.
Learn the underlying Python first with the [official tutorial](https://docs.python.org/3/tutorial/).
