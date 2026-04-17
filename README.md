# Meta<Claw>

This is an installation framework for personal AI agents, meant to allow
non-technical individuals to install a large number of powerful tools that
together provide safe, secure, cost-effective, personal AI capabilities.
This framework focuses predominantly on OpenClaw and the large ecosystem
of external-to-OpenClaw tools that it uses, leaving OpenClaw-specific
customization up to the individual user. The goal is to get a user able to
interact with OpenClaw (or other personal AI gateway) with as little effort
as possible, so they can focus all of their time on creating and interacting
with their agents instead of learning how to setup, configure, maintain, and
synchronize the details of how OpenClaw talks to AI models, runs local models,
efficiently stores and indexes memories, and many other things needed for a
safe, efficient, cost-effective AI environment.

## Services

The various external-to-OpenClaw services and technologies supported by
Meta<Claw> have been categorized according to their use within OpenClaw, and
each such category is called a _service_. Each service is fulfilled by one of
a variety of (usually mutually exclusive) concrete _providers_. For example,
the AI gateway itself is considered a service, with one provider being
OpenClaw, but many others available to explore as well (NemoClaw, PicoClaw,
etc).

Because of the large number of services, and the even larger number of
providers for each service, Meta<Claw> is by definition a work-in-progress,
with support for specific service/provider pairs being added when someone
in the Meta<Claw> community wants to explore it. The initial version of
Meta<Claw> makes a specific choice for which provider to use for each
service (usually aimed at an end-user running OpenClaw on their local laptop).

As the user starts exploring more and more of what OpenClaw can do, they can
graduate to more sophisticated/advanced providers for each service. Here
are the services Meta<Claw> supports:

- Gateway (e.g., OpenClaw, Moltis, n8n)
- AI Proxy (e.g., LiteLLM, OpenRouter, Manifest)
- LLM Runner (e.g., Ollama, vLLM, llama.cpp)
- Memory (e.g., PostgreSQL+pgvector, Qdrant)
- Cache (e.g., Redis, Turso)
- Log Aggregation (e.g., VictoriaLogs, Loki)
- Sandboxing (e.g., gVisor, E2B)
- Overlay Networks (e.g., Tailscale, ZeroTier)
- Browser Automation (e.g., Playwright, Browser Use)
