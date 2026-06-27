# MetaClaw

This is an installation framework for personal AI agents, meant to allow
non-technical individuals to install a large number of powerful tools that
together provide safe, secure, cost-effective, personal AI capabilities.
This framework focuses predominantly on OpenClaw and the large ecosystem
of external-to-OpenClaw tools that it uses, leaving OpenClaw-specific
customization up to the individual user.

**Our Philosophy:** MetaClaw is designed to be unobtrusive and un-opinionated.
Our primary goal is to make it incredibly easy for non-technical people to get
up and running with a production-grade OpenClaw environment, *without* putting
them in an architectural straight-jacket. Once the infrastructure is running,
the framework gets out of your way, granting you full autonomy to design your
agents however you see fit.

## Services

The various external-to-OpenClaw services and technologies supported by
MetaClaw have been categorized according to their use within OpenClaw, and
each such category is called a _service_. Each service is fulfilled by one of
a variety of (usually mutually exclusive) concrete _providers_. For example,
the AI gateway itself is considered a service, with one provider being
OpenClaw, but many others available to explore as well (NemoClaw, PicoClaw,
etc).

Because of the large number of services, and the even larger number of
providers for each service, MetaClaw is by definition a work-in-progress,
with support for specific service/provider pairs being added when someone
in the MetaClaw community wants to explore it. The initial version of
MetaClaw makes a specific choice for which provider to use for each
service (usually aimed at an end-user running OpenClaw on their local laptop).

As the user starts exploring more and more of what OpenClaw can do, they can
graduate to more sophisticated/advanced providers for each service. Here
are the services MetaClaw supports:

- AI Gateway (`gateways`)
  - Providers: OpenClaw (`openclaw`), Moltis (`moltis`), n8n (`n8n`)
  - Summary: The core intelligence layer acting as the user-facing agent
    framework that handles tool definitions, workflow execution, and multi-agent
    routing.
- AI Proxy (`proxies`)
  - Providers: LiteLLM (`litellm`), OpenRouter (`openrouter`), Manifest (`manifest`)
  - Summary: Middleware between the Gateway and external LLMs, acting as a
    central control plane for cost management, load balancing, and guarding API
    keys.
- LLM Runner (`runners`)
  - Providers: Ollama (`ollama`), vLLM (`vllm`), llama.cpp (`llamacpp`)
  - Summary: Manages and executes local Large Language Models and Multimodal
    models directly on bare-metal hardware for offline intelligence.
- Long-Term Memory (`memories`)
  - Providers: PostgreSQL (`postgres`), Qdrant (`qdrant`), Milvus (`milvus`)
  - Summary: The permanent, space-efficient archive for the agent supporting
    high-dimensional vector embeddings for semantic search alongside standard
    relational data.
- Real-Time Cache (`caches`)
  - Providers: Redis (`redis`), Turso (`turso`), Convex (`convex`)
  - Summary: Ultra-low latency ephemeral storage used for semantic caching,
    session states, multi-agent communication, and distributed locking.
- Log Aggregator (`loggers`)
  - Providers: VictoriaLogs (`victorialogs`), Loki (`loki`), SigNoz (`signoz`)
  - Summary: The central repository for system logs, providing real-time
    visibility to monitor agent behavior and audit actions.
- Overlay Network (`networks`)
  - Providers: Tailscale (`tailscale`), ZeroTier (`zerotier`), Cloudflare Tunnels (`cloudflare-tunnels`)
  - Summary: Provides zero-trust mesh networking and secure inbound routing to
    access the AI cluster remotely without exposing router ports.
- Browser Automation (`browsers`)
  - Providers: Browser Use (`browseruse`), Stagehand (`stagehand`), Skyvern (`skyvern`)
  - Summary: Provides advanced, AI-driven DOM interaction, visual
    interpretation, and self-healing autonomous navigation capabilities.
- Execution Sandbox (`sandboxes`)
  - Providers: Docker DooD (`docker-dood`), gVisor (`gvisor`), E2B (`e2b`)
  - Summary: Hardened execution environments designed to contain the blast
    radius of agent actions and volatile code generation.
- Secrets Manager (`secrets`)
  - Providers: Doppler (`doppler`), Bitwarden (`bitwarden`), Vault (`vault`)
  - Summary: A centralized, encrypted vault that securely stores and injects
    third-party API keys directly into the agent's runtime memory.
- Identity & Access Management (`iam`)
  - Providers: Authelia (`authelia`), Keycloak (`keycloak`), Authentik (`authentik`)
  - Summary: The authentication gatekeeper enforcing MFA and SSO at the reverse
    proxy layer to secure the dashboard from unauthorized internet access.
- Distributed Tracer (`tracers`)
  - Providers: Langfuse (`langfuse`), OpenTelemetry (`opentelemetry`), SigNoz (`signoz`)
  - Summary: Measures execution duration across services to debug latency
    bottlenecks in complex, multi-step agent trajectories.
- Web Fetcher (`fetchers`)
  - Providers: Crawl4AI (`crawl4ai`), Firecrawl (`firecrawl`), Jina AI Reader (`jinareader`)
  - Summary: Bypasses anti-bot measures to fetch, render, and extract clean,
    LLM-ready markdown or JSON from specific URLs.
- Web Search API (`searchers`)
  - Providers: SearXNG (`searxng`), Exa (`exa`), Tavily (`tavily`)
  - Summary: Executes high-speed, lightweight HTTP searches to return structured
    snippets, URLs, and real-time knowledge context.
- Continuous Integration (`ci`)
  - Providers: Woodpecker (`woodpecker`), Drone (`drone`), GitHub Actions (`github-actions`)
  - Summary: The automated testing pipeline that proves agent-generated code
    works against a test suite before it is deployed.
- Message Queue (`queues`)
  - Providers: RabbitMQ (`rabbitmq`), Kafka (`kafka`), NATS (`nats`)
  - Summary: The asynchronous task broker that decouples the Gateway from
    execution nodes to prevent HTTP timeouts during long-running workloads.
- Event Gateway (`events`)
  - Providers: Hookdeck (`hookdeck`), Svix (`svix`), ngrok (`ngrok`)
  - Summary: Securely ingests, queues, and standardizes incoming webhooks from
    the outside world to wake up the agent asynchronously.
- Reverse Proxy (`proxies-reverse`)
  - Providers: Caddy (`caddy`), Traefik (`traefik`), Nginx (`nginx`)
  - Summary: The network front door handling SSL termination, load balancing,
    and rate limiting for the local AI ecosystem.
- Version Control System (`vcses`)
  - Providers: Forgejo (`forgejo`), Gitea (`gitea`), GitLab (`gitlab`)
  - Summary: The immutable state capture layer that tracks all code
    modifications and documentation updates generated by autonomous agents.
