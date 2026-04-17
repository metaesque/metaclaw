# MetaClaw Service Ecosystem

This document serves as the canonical registry for the critical infrastructure
services that make up the MetaClaw framework.

## Planes

### The Control Plane {#control}

* **Aka**: The Ingress & Routing Hub
* **Profile**: High network I/O, low CPU, low RAM.
* **Justification**: This is the high-speed nervous system. It dictates traffic
  flow and maintains ephemeral state, operating flawlessly on low-power devices.
* **Services**: proxy-reverse, iam, proxy, gateway, secret, event, cache, queue

### The Compute Plane {#compute}

* **Aka**: The Intelligence Engine
* **Profile**: Extreme GPU VRAM, maximum memory bandwidth, high power draw.
* **Justification**: LLM inference requires dedicated PCIe acceleration. It must
  be isolated to prevent VRAM starvation from impacting other critical services.
* **Services**: runner

### The Archive Plane {#archive}

* **Aka**: Context & Telemetry
* **Profile**: Massive RAM capacity, extreme disk IOPS (NVMe), heavy storage.
* **Justification**: This plane manages all "Trusted Data." Vector databases
  ingest massive streams of data and require enormous RAM. Keeping these safe
  from untrusted execution workloads is a strict SRE requirement.
* **Services**: memory, vcs, logger, tracer

### The Execution Plane {#execution}

* **Aka**: The Blast Zone
* **Profile**: Heavy multi-core CPU, highly dynamic and unpredictable RAM usage.
* **Justification**: This plane executes volatile, untrusted code. It is an
  operational hazard physically isolated to ensure that a rogue task cannot
  crash the Control Plane or corrupt the Data Plane.
* **Services**: browser, fetcher, searcher, sandbox, ci

## Phases

### Phase 0: The Day 1 Minilith {#phase-0}

* **Setup**: RAM is strictly budgeted (6GB-8GB). The framework uses lightweight
  alternatives (SQLite instead of Postgres, LiteLLM routing to Cloud APIs for
  heavy reasoning, Ollama strictly for local text embeddings).
* **Benefit**: Zero financial cost to validate the framework's utility.

### Phase 1: The Month 2 Monolith {#phase-1}

* **Setup**: All four Planes run on one machine. Heavy services are rate-limited
  via Docker to prevent crashes. the Compute Plane remains outsourced to Cloud
  APIs.
* **Benefit**: True 24/7 autonomous operation with robust relational memory and
  background web scraping.

### Phase 2: Data Sovereignty {#phase-2}

* **Setup**: Tier 2 (LLM Runner) is migrated to the GPU tower. The Proxy routes
  requests locally.
* **Benefit**: Absolute data privacy and zero recurring API costs. Infinite
  agent loops can run overnight without accumulating massive bills.

### Phase 3: The Sandbox Extraction {#phase-3}

* **Setup**: Tier 4 (Execution Plane) is migrated.
* **Benefit**: Safe execution of highly volatile workloads. Hallucinated code or
  memory-leaking browsers will not crash the core Gateway.

### Phase 4: The Archive Expansion {#phase-4}

* **Setup**: The Archive Plane is migrated. The original Month 2 Monolith is
  stripped of heavy workloads, running strictly as the Control Plane.
* **Benefit**: SRE-grade stability with near-infinite, lightning-fast semantic
  recall. No hardware is wasted; earlier machines are perfectly repurposed.

## Services

### Security & Containment

#### Execution Sandbox {#sandboxes}

* **Path**: `services/sandboxes/`
* **Purpose**: Hardened execution environments designed to contain the blast
  radius of agent actions. If an agent hallucinates a dangerous Python or Bash
  script, this layer prevents that code from escaping and destroying the host
  machine. (Standard Docker is insufficient here).
* **Options**: Docker, gVisor, Hardened Docker DooD, Firecracker, E2B.

#### Secrets Manager {#secrets}

* **Path**: `services/secrets/`
* **Purpose**: A centralized, encrypted vault. It securely stores and injects
  third-party API keys (e.g., AWS, GitHub, Stripe) directly into the agent's
  runtime memory, ensuring secrets never leak into plaintext logs or
  configuration files.
* **Options**: Doppler, Infisical, Bitwarden Secrets Manager, HashiCorp Vault.

#### Overlay Network {#networks}

* **Path**: `services/networks/`
* **Purpose**: Provides zero-trust mesh networking and secure inbound routing.
  It allows you to access your AI cluster remotely without exposing router
  ports, and allows external services (like Google Chat webhooks) to securely
  POST data to your local gateway through CGNAT firewalls.
* **Options**: Cloudflare Tunnels, Tailscale, ZeroTier.

#### Identity & Access Management {#iam}

* **Path**: `services/iam/`
* **Purpose**: The authentication gatekeeper. Enforces Multi-Factor
  Authentication (MFA) and Single Sign-On (SSO) at the reverse proxy layer,
  ensuring unauthorized users cannot access the OpenClaw dashboard from the
  internet.
* **Options**: Authentik, Authelia, Keycloak.

### Observability & Provenance

#### Log Aggregator {#loggers}

* **Path**: `services/loggers/`
* **Purpose**: The central repository for system logs. It provides the
  visibility required to monitor agent behavior in real-time, troubleshoot tool
  execution errors, and audit actions when the agent is granted deep system
  access.
* **Options**: Grafana Loki, SigNoz, Graylog, OpenSearch, Quickwit, ELK Stack,
  Fluent Bit, VictoriaLogs, Vector.

#### Version Control System {#vcs}

* **Path**: `services/vcs/`
* **Purpose**: The source of truth for workspace files. It tracks every code
  change efficiently and provides strict agent attribution (via Git signatures),
  answering the question: "What exactly did the AI alter while I was asleep?"
* **Options**: GitLab, Gitea, GitHub, OneDev, Codeberg, Bitbucket, Forgejo,
  Gogs, SourceHut, Git (CLI native).

#### Distributed Tracer {#tracers}

* **Path**: `services/tracers/`
* **Purpose**: While logging tells you what happened, tracing tells you how long
  it took. It measures execution duration across services (Gateway -> Proxy ->
  LLM Runner) to debug latency bottlenecks in complex multi-step trajectories.
* **Options**: Langfuse, SigNoz, OpenTelemetry Collector + Jaeger, Phoenix.

### Intelligence Execution

#### Web Fetcher {#fetchers}

* **Path**: `services/fetchers/`
* **Purpose**: Bypasses anti-bot measures to fetch, render, and extract clean,
  LLM-ready markdown or JSON from specific URLs.
* **Options**: Crawl4AI, Firecrawl, Browse AI, Jina AI Reader, Zyte, Octoparse,
  ScrapeGraphAI.

#### Web Search API {#searchers}

* **Path**: `services/searchers/`
* **Purpose**: Executes high-speed, lightweight HTTP searches to return
  structured snippets, URLs, and real-time knowledge.
* **Options**: Exa, SearXNG, Brave Search API, Linkup, Parallel AI Search,
  Tavily.

#### Browser Automation {#browsers}

* **Path**: `services/browsers/`
* **Purpose**: Provides advanced, AI-driven DOM interaction, visual
  interpretation, and self-healing autonomous navigation capabilities.
* **Options**: Steel Browser, Browser Use, Agent Browser, LaVague, Stagehand,
  Hyperbrowser, Skyvern.

#### LLM Runner {#runners}

* **Path**: `services/runners/`
* **Purpose**: Manages and executes local Large Language Models (LLMs) and
  Multimodal models directly on your bare-metal hardware. It provides an OpenAI-
  compatible API endpoint for the AI Proxy or Gateway to consume, enabling
  offline intelligence.
* **Options**: LM Studio, Text-Gen-WebUI, llama.cpp, LocalAI, Jan.ai, KoboldCPP,
  vLLM, Msty, Ollama, GPT4All.

### Decoupling & Workflow

#### Continuous Integration {#ci}

* **Path**: `services/ci/`
* **Purpose**: The automated testing pipeline. It triggers automated builds and
  test suites on any code generated by the autonomous agent, mathematically
  proving the code works before it is deployed to production.
* **Options**: GitLab CI/CD, Gitea/Drone, Woodpecker CI, Jenkins, BitBucket
  Pipelines, Buildkite, GitHub Actions.

#### Message Queue {#queues}

* **Path**: `services/queues/`
* **Purpose**: The asynchronous task broker. It decouples the Gateway from the
  execution nodes. Instead of waiting synchronously (which causes HTTP timeouts
  if a local model takes 60 seconds to reply), the Gateway pushes tasks to a
  queue for worker nodes to consume at their own pace.
* **Options**: Redis Streams, RabbitMQ, NATS, Apache Kafka.

#### Event Gateway {#events}

* **Path**: `services/events/`
* **Purpose**: The external signal receiver. It securely ingests, queues, and
  standardizes incoming webhooks from the outside world (like emails, calendar
  alerts, or smart home triggers) to wake up the agent and trigger workflows
  asynchronously.
* **Options**: Custom ngrok endpoints, Svix, Hookdeck.

### Orchestration & Routing

#### Reverse Proxy {#proxies-reverse}

* **Path**: `services/proxies-reverse/`
* **Purpose**: The network front door. It handles SSL termination, load
  balancing incoming external requests, rate limiting, and securely exposing
  your local AI ecosystem to the internet for remote access.
* **Options**: Nginx, Caddy, Traefik, HAProxy.

#### AI Gateway {#gateways}

* **Path**: `services/gateways/`
* **Purpose**: The core intelligence layer. This is the user-facing agent
  framework that handles tool definitions, semantic memory retrieval, workflow
  execution, and multi-agent routing.
* **Options**: Moltis, NanoClaw, OpenClaw, TrustClaw, Knolli AI, Claude Code,
  Nanobot, NullClaw, ZeroClaw, n8n + AI, PicoClaw, Manis AI.

#### AI Proxy {#proxies}

* **Path**: `services/proxies/`
* **Purpose**: The middleware sitting between the Gateway and external LLM
  providers. It acts as a central control plane for cost management, enforcing
  guardrails, load balancing requests, and masking raw API keys from the agent.
* **Options**: Portkey, OpenRouter, Helicone, Manifest, TrueFoundry, Bifrost,
  LiteLLM.

### Data & State Management

#### Long-Term Memory {#memories}

* **Path**: `services/memories/`
* **Purpose**: The permanent, space-efficient archive for the agent. This
  database must support high-dimensional vector embeddings for semantic search
  (associative recall) alongside standard relational data (configs, logs).
* **Options**: SQLite, PostgreSQL + pgvector, Qdrant, Weaviate, Milvus.

#### Real-Time Cache {#caches}

* **Path**: `services/caches/`
* **Purpose**: Ultra-low latency, ephemeral storage. It is used for semantic
  caching (to save money on repeated API queries), maintaining short-term
  session states, facilitating multi-agent pub/sub communication, and
  distributed locking.
* **Options**: Redis, Context Lakes, Turso, Convex, Memcached, Memori Labs.
