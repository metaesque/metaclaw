# OpenClaw Framework: Service Expansion Roadmap

*Note: With the upgrade to OpenClaw 2026.6.8, Meta<Claw> has formally adopted an "un-opinionated" design goal.
We aim to make it incredibly easy for non-technical users to get OpenClaw running, without placing them in a straight-jacket once the environment is operational.
All future roadmap items are evaluated against this ethos.*

This document outlines the prioritized architectural strategy for integrating future software capabilities and migrating across hardware tiers.

---

## 🟢 MILESTONE 1: The Tier 0 Foundation (Achieved)

**Status: COMPLETED (`stable-v1`)**
**Public Repository:** [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw)

**The Accomplishment:** We have successfully built and verified a working Tier 0 environment.
MetaClaw now reliably bootstraps OpenClaw alongside its essential caching and observability services.
We have transitioned framework development natively into the local OpenClaw agent workflow, granting it read/write workspace access to iteratively improve the ecosystem.

---

## 🟡 MILESTONE 2: The Tier 1 & Tier 2 Linux Migration

**Urgency: HIGH**
**Status: IN PROGRESS**

**Current Hardware State:**
The dedicated edge hardware has been successfully physically provisioned.
Both nodes are running headless Ubuntu Server, are accessible remotely via Tailscale, can be managed seamlessly via Emacs TRAMP, and have the `metaesque/metaclaw` repository cloned into the `metaclaw` user's `$HOME` directory.
* **The Control Node:** GMKtec K8 Plus
* **The Compute Node:** GMKtec EVO X2

### Step A: Evolve the Control Node (Tier 2 Control Plane)
**Status: Mostly Complete (July 1, 2026).** The node successfully boots, handles remote Tailscale HTTPS UI access, and responds to prompts.
Comprehensive testing of fetchers/searchers is pending.
1. **Ubuntu Optimization:** Refactored Makefiles and deployment scripts to account for headless Ubuntu constraints (e.g., bare-metal Tailscale lifelines, WebCrypto HTTPS requirements).
2. **Provider Diversification:** Expanded the `services` architecture to support robust, bare-metal or heavy-docker providers (PostgreSQL pgvector, VictoriaLogs, LiteLLM).

### Step B: Evolve the Compute Node (Tier 2 Compute Plane)
**Status: PENDING (Next Immediate Step).**
We must configure the EVO X2 to act as the dedicated **Tier 2 LLM Runner** to eliminate expensive API costs for trivial agent actions.
1. **Local Model Hosting:** Configure the LLM Runner (Ollama or vLLM) to utilize the EVO X2's Strix Halo APU and unified memory for high-speed local inference.
2. **Proxy Routing Matrix:** Update LiteLLM's `config.yaml` on the Control Node to route `simple-model` tasks (e.g., tool execution) to small, fast models on the K8 Plus, while routing `complex-model` tasks to massive reasoning models (e.g., Llama 4 109B) over the LAN to the EVO-X2.
3. **Hot/Cold Swapping:** Establish logic/timeout protocols within the runners to seamlessly swap specialized models (vision, code) into VRAM when required and evict them when idle.

---

## 🟢 MILESTONE 3: The Modular Routing & Un-opinionated Customization Refactor

**Urgency: HIGH**
**Status: COMPLETED (July 2, 2026)**

As MetaClaw transitioned from an opinionated script into a general-purpose facilitator, we decoupled the rigid `openclaw.json` overwrites in favor of dynamic user customization.
**The Accomplishments:**
1. **The Sibling Directory Architecture:** We formally decoupled the user's data from the MetaClaw repository.
The workspace now lives in `../workspace` and the databases in `../external`, completely isolating the user from destructive `git clean` operations.
2. **Interactive Bootstrapping:** `bin/customize.py` now allows users to cleanly select their preferred Prompt Routing Strategy and automatically hydrates an empty workspace from a `.workspace.template` if requested.
3. **Native Workspace Routing Plugins:** We abandoned the brittle JSON injection method for Prompt Routing.
Instead of hacking `openclaw.json`, MetaClaw now compiles Lexical/Predictive JS logic into an official `openclaw.plugin.json` package directly inside the user's workspace (`.openclaw/extensions/metaclaw-routing`).
OpenClaw natively discovers and loads this plugin during boot, allowing the system to use a local LLM Judge to intercept prompts and deflect them away from expensive Gemini API calls seamlessly.

---

## 🟡 MILESTONE 4: The CLI-First Configuration Refactor

**Urgency: MEDIUM**
**Status: PLANNED**

**Purpose:** To firmly establish MetaClaw as a facilitator rather than a dictator, we must migrate away from direct programmatic modification of `openclaw.json`. Hacking JSON keys directly is brittle across point-releases, risks corrupting the configuration (causing crash loops), and obscures the native mechanisms from the end-user.

Instead, we will configure the Gateway using official OpenClaw CLI commands (e.g., `openclaw config set`, `openclaw agents add`). This strategy is more resilient, future-proof, and models best practices for users wanting to add agents themselves.

**The Role of YAML files in the Refactor:**
OpenClaw natively reads Markdown files (`SOUL.md`, `AGENTS.md`) for system prompts, but it does NOT natively read YAML files or frontmatter for configuration metadata. Therefore, we will retain the custom agent `.yaml` files in the workspace purely as Infrastructure-as-Code manifests. A Python bootstrapping script will parse these `.yaml` files to extract the `model`, `tools`, and `workspace` metadata, and then execute the corresponding `openclaw agents add` CLI commands in bulk to dynamically populate the gateway configuration on a fresh installation.

**Target Files for Cleanup:**
* `services/gateways/openclaw/patch_routing.py` (Must be refactored to utilize `subprocess.run` wrapping `openclaw config set` rather than direct JSON object manipulation).

---

## Phase 1: Safe Execution (Sandboxing)

* **Category:** `services/sandboxes/`
* **Target Providers:** `gVisor` (Local Linux hardening), `E2B` (Cloud ephemeral execution).
* **Purpose:** Move beyond the basic `docker-dood` implementation to prevent malicious or hallucinated agent code from escaping the container namespaces and corrupting the host OS.

## Phase 2: External Interaction (Browsers, Fetchers, and Searchers)

* **Categories:** `services/browsers/`, `services/fetchers/`, `services/searchers/`
* **Purpose:** Expand the Tier 0 demonstration capabilities into robust 24/7 background tasks.
Implement visual DOM interpretation (`Skyvern`), action-caching to save API costs (`Stagehand`), and self-healing data extraction that doesn't break when CSS classes change.

## Phase 3: Source Truth & Reliability (VCS & CI)

* **Category:** `services/vcses/` & `services/ci/`
* **Target Providers:** `Forgejo / Gitea`, `Woodpecker CI / Drone`
* **Purpose:** As agents autonomously modify workspace files, we need absolute attribution.
CI pipelines will mathematically prove the agent's code works against a test suite before it is deployed.
Note: The `vcses` service currently has no providers implemented and needs initial integrations added.

## Phase 4: Decoupling & Debugging (Queues & Tracing)

* **Category:** `services/queues/` & `services/tracers/`
* **Target Providers:** `RabbitMQ`, `OpenTelemetry + Jaeger / SigNoz`
* **Purpose:** Prevent timeouts during complex multi-agent swarms by decoupling synchronous HTTP calls.
Provide deep visibility into latency spans to debug slow agent reasoning loops.

## Phase 5: Secure Public Ingress (Reverse Proxy & IAM)

* **Categories:** `services/proxies-reverse/`, `services/iam/`
* **Target Providers:** `Traefik / Caddy`, `Authelia / Authentik`
* **Purpose:** Expose specific agent endpoints (like a shared public webhook receiver) to external users via strict Multi-Factor Authentication and SSL termination.
