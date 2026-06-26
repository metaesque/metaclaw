# LLM Runner Overview

## Providers

### LM Studio
Moderate/Low Utility. These are desktop GUI applications first, and API servers
second. While their local APIs work perfectly fine with OpenClaw, running an
entire Electron/React desktop app just to serve an API to a background agent
framework is inefficient and counter to OpenClaw's architecture. They are great
for testing models, but poor for permanent OpenClaw integration.

### Text-Gen-WebUI
Moderate Utility. While the UI is irrelevant to OpenClaw, its support for the
ExLlamaV2 loader is crucial. For users with high-end Nvidia GPUs who want the
absolute fastest tokens-per-second on local hardware, pointing OpenClaw at the
WebUI API running an EXL2 model is the power-user optimal path.

### llama.cpp
High Utility. The raw foundation. For OpenClaw nodes deployed on Raspberry Pis
or edge servers, running the bare llama.cpp server provides the lowest-overhead,
most memory-efficient API endpoint possible.

### LocalAI
High Utility. OpenClaw uses tools heavily (Voice TTS, Vision, Image Generation).
Because LocalAI serves as a drop-in OpenAI replacement for *all* these
modalities, it allows a user to run a completely offline, full-featured OpenClaw
deployment without configuring separate providers for every tool.

### Jan.ai
Moderate/Low Utility. These are desktop GUI applications first, and API servers
second. While their local APIs work perfectly fine with OpenClaw, running an
entire Electron/React desktop app just to serve an API to a background agent
framework is inefficient and counter to OpenClaw's architecture. They are great
for testing models, but poor for permanent OpenClaw integration.

### KoboldCPP
Moderate Utility. OpenClaw's heavy reliance on reading `MEMORY.md` and
transcript history means context sizes get large quickly. KoboldCPP's
ContextShift feature saves massive amounts of compute by not reprocessing the
prompt on every turn, making OpenClaw noticeably more responsive on consumer
hardware.

### vLLM
High Utility (Niche). If you are running OpenClaw on a dedicated VPS with A100s
and relying heavily on sub-agent swarms (`sessions_spawn`), vLLM is unmatched.
Its PagedAttention algorithm will handle the concurrent agent tasks faster than
anything else on the market.

### Msty
Moderate/Low Utility. These are desktop GUI applications first, and API servers
second. While their local APIs work perfectly fine with OpenClaw, running an
entire Electron/React desktop app just to serve an API to a background agent
framework is inefficient and counter to OpenClaw's architecture. They are great
for testing models, but poor for permanent OpenClaw integration.

### Ollama
Highest Utility. Ollama perfectly mirrors OpenClaw's daemon-based architectural
philosophy. It runs headlessly, manages hardware gracefully, and is natively
supported by OpenClaw's LiteLLM backend (`ollama/model`). It is the undisputed
default for local OpenClaw deployments.

### GPT4All
Lowest Utility. While excellent for CPU-only privacy enthusiasts, its ecosystem
is highly curated and restrictive compared to the open Wild West of Hugging
Face. Its API is functional for OpenClaw, but Ollama or native llama.cpp
generally handle CPU fallbacks better with vastly superior model selection.
