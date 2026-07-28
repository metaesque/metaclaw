# MetaClaw Roadmap

## TOP PRIORITY: Orchestrator DAG Delegation
**Goal:** Successfully send the "Design a Flutter application..." prompt to the `software_orchestrator` agent.
**Requirement:** The local `llama4-scout-q4:109b` model must generate a valid Directed Acyclic Graph (DAG) and properly perform structured tool calls to delegate tasks to `software_dev` and `software_qa`.
**Blocker:** Ollama is currently returning the tool payload as raw JSON text in the `content` field instead of a native OpenAI `tool_calls` array due to a custom Modelfile template override.

## Upcoming Milestones
1. Implement a LiteLLM Proxy middleware (or strict JSON schema constraint) to reliably format Llama 4 Scout JSON output into native tool calls.
2. Validate DAG execution across multiple agent instances.
3. Finalize spend tracking and Auditor integration.
