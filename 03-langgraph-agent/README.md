# Project 03: LangGraph agents and MCP

**Status: scaffold only. Implementation is Steps 4 and 5.**
Start with the working [shared-layer lesson](../README.md#run-your-first-request).

An agent chooses actions. A graph controls how those choices are executed and when
the process stops. We will make that control visible before adding complex tools.

| Planned example in `examples/` | Learning goal |
|---|---|
| `01_hello_graph.py` | Typed state, two plain nodes, edges, START and END |
| `02_chatbot_graph.py` | Model messages and an accumulating message reducer |
| `03_tool_calling.py` | Model → tool → model loop with a conditional edge |
| `04_multi_tool_agent.py` | Document search, web, Wikipedia, calculator, weather and time |
| `05_memory.py` | In-memory then SQLite checkpoints, selected by thread ID |
| `06_human_in_the_loop.py` | Interrupt and approve a simulated email action |
| `07_agentic_rag.py` | Route, retrieve, grade, rewrite, generate and check grounding |
| `08_mcp_integration.py` | Connect an MCP server's tools alongside local tools |

The simulated email tool will not send real messages. Agent loops will have explicit
limits. The Streamlit app will expose enabled tools, steps, memory and approval state.
None of these agent features is implemented yet.

MCP is a standard connection for tools and data. LangGraph controls a workflow; MCP
connects that workflow to external capabilities. They serve different purposes and
can work together. Learn more from the [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview).
