# openrouter: OpenRouter

## Overview

OpenRouter is a unified AI proxy and model marketplace that allows users to
access hundreds of different LLMs through a single API endpoint. Unlike self-
hosted gateways, OpenRouter is a fully managed cloud service that aggregates
models from major providers alongside an extensive collection of open-source
models hosted on various cloud platforms. It standardizes the interface so that
all interactions use the familiar OpenAI Chat Completions format.

One of the primary advantages of OpenRouter is its streamlined billing and
access model. Instead of maintaining separate accounts, API keys, and payment
methods for dozens of different AI companies, developers only need a single
OpenRouter account to pay for exactly what they use. The platform also offers
smart routing capabilities, allowing users to automatically direct requests to
the cheapest or fastest provider hosting a specific open-source model at any
given moment.

For OpenClaw users, OpenRouter represents the absolute lowest-friction way to
experiment with different models. By simply setting OpenClaw's base URL to
OpenRouter and providing a single API key, the agent immediately gains the
ability to seamlessly swap between models like Claude 3.5 Sonnet, Llama 3, or
Gemini just by changing the model string name. It is highly practical for users
who want maximum model diversity for their OpenClaw agent without the
operational overhead of running their own local proxy infrastructure.
