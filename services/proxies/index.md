# AI Proxy Overview

## Providers

### Portkey


### OpenRouter
OpenRouter ranks highly simply for its zero-friction utility. If you do not want
to manage proxy infrastructure, OpenRouter is the best choice. With a single API
key plugged into OpenClaw, you instantly gain access to top-tier proprietary
models and cutting-edge open-source models, making it the best option for
developers who want to experiment with different models rapidly.

### Helicone
Helicone is the ultimate choice for developers who are building custom skills
for OpenClaw and need to debug them. Because... (truncated)

### Manifest
Manifest takes the top spot because it was specifically engineered with AI
agents like OpenClaw in mind. Its session-aware routing prevents "tier
oscillation" (where a multi-turn task bounces between a smart model and a dumb
model mid-thought), which is crucial for OpenClaw's chain-of-thought tool
calling. It is the most native-feeling routing solution for agentic workflows.

### TrueFoundry


### Bifrost


### LiteLLM
LiteLLM is the gold standard for general-purpose, open-source proxying. It is
incredibly easy to spin up locally (e.g., via Docker) alongside OpenClaw, and
its strict adherence to OpenAI compatibility ensures that OpenClaw's tool-
calling formats never break when translated to models like Claude or Gemini. It
handles 99% of what OpenClaw needs flawlessly.
