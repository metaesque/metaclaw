# MetaClaw Architecture

## Core Philosophy
MetaClaw is a hermetic, localized AI orchestration framework. It isolates all dependencies (including LLM runners like Ollama) from the host OS to prevent port conflicts and version lag.

## Components
- **Control Plane:** Hosts the LiteLLM proxy and lightweight judge/router models (e.g., Gemma 4).
- **Compute Plane:** Hosts heavy local models (e.g., Qwen 3, Llama 4 Scout 109B) on dedicated hardware (e.g., EVO-X2).
- **OpenClaw Interface:** The GUI and agent orchestration layer.

## Known Architectural Quirks
- **Ollama Tool Calling:** Overriding the default GGUF template in a Modelfile disables Ollama's native tool-call regex interceptor. The model will output clean JSON, but it will be passed to LiteLLM as raw text (`content`) instead of a structured `tool_calls` object.
