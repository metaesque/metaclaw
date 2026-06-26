# litellm: LiteLLM

## Overview

LiteLLM is a highly popular, open-source AI proxy and gateway provider that
provides a unified, OpenAI-compatible API for over 100 different Large Language
Model (LLM) providers. By standardizing the input and output formats across
providers like Anthropic, Google, Mistral, and Azure, it eliminates the need for
developers to write provider-specific API integrations. This allows applications
to seamlessly interact with virtually any model on the market using standard
OpenAI SDKs and connection protocols.

Beyond simple translation, LiteLLM functions as a robust operational gateway
designed for production environments. It offers essential features such as load
balancing across multiple API keys, automatic fallbacks to ensure reliability
during provider outages, and semantic caching to reduce costs on repeated
queries. Additionally, it provides built-in rate limiting, cost tracking, and
spend controls, making it an effective tool for managing organizational LLM
usage.

Within an OpenClaw environment, LiteLLM serves as an incredibly versatile middle
layer. By pointing OpenClaw's primary endpoint to a self-hosted LiteLLM proxy,
users can instantly grant the agent access to a vast array of local and cloud-
based models without altering OpenClaw's internal configuration. Its seamless
OpenAI compatibility ensures that OpenClaw's system prompts, complex tool-
calling structures, and message histories are accurately and reliably passed to
whichever backend provider is currently selected.

<h2 id="diagnostic-checks">Diagnostic Checks (proxy litellm)</h2>
1. **Web Server Health:** You should see `200`
2. **Model Inventory:** You should see `simple-model`, `medium-model`, and others
