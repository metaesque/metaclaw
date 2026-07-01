# OpenClaw Framework: Service Expansion Roadmap

*Note: With the upgrade to OpenClaw 2026.6.8, Meta<Claw> has formally adopted an "un-opinionated" design goal. We aim to make it incredibly easy for non-technical users to get OpenClaw running, without placing them in a straight-jacket once the environment is operational. All future roadmap items are evaluated against this ethos.*

This document outlines the prioritized architectural strategy for integrating future software capabilities and migrating across hardware tiers.

---

## 🟢 MILESTONE 1: The Tier 0 Foundation (Achieved)

**Status: COMPLETED (`stable-v1`)**
**Public Repository:** [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw)

**The Accomplishment:** We have successfully built and verified a working Tier 0 environment. MetaClaw now reliably bootstraps OpenClaw alongside its essential caching and observability services. We have transitioned framework development natively into the local OpenClaw agent workflow, granting it read/write workspace access to iteratively improve the ecosystem.

---

## 🟡 MILESTONE 2: The Tier 1 & Tier 2 Linux Migration

**Urgency: HIGH**
**Status: IN PROGRESS**

**Current Hardware State:**
The dedicated edge hardware has been successfully physically provisioned. Both nodes are running headless Ubuntu Server, are accessible remotely via Tailscale, can be managed seamlessly via Emacs TRAMP, and have the `metaesque/metaclaw` repository cloned into the `metaclaw` user's `$HOME` directory.
* **The Control Node:** GMKtec K8 Plus
* **The Compute Node:** GMKtec EVO X2

### Step A: Evolve the Control Node (Tier 2 Control Plane)
**Status: Mostly Complete (July 1, 2026).** The node successfully boots, handles remote Tailscale HTTPS UI access, and resolves basic prompts. Comprehensive testing of fetchers/searchers is pending.
1. **Ubuntu Optimization:** Refactored Makefiles and deployment scripts to account for headless Ubuntu constraints (e.g., bare-metal Tailscale lifelines, WebCrypto HTTPS requirements).
2. **Provider Diversification:** Expanded the `services` architecture to support robust, bare-metal or heavy-docker providers (PostgreSQL pgvector, VictoriaLogs, LiteLLM).

### Step B: Evolve the Compute Node (Tier 2 Compute Plane)
**Status: PENDING (Next Immediate Step).**
We must configure the EVO X2 to act as the dedicated **Tier 2 LLM Runner** to eliminate expensive API costs for trivial agent actions.
1. **Local Model Hosting:** Configure the LLM Runner (Ollama or vLLM) to utilize the EVO X2's Strix Halo APU and unified memory for high-speed local inference.
2. **Proxy Routing Matrix:** Update LiteLLM's `config.yaml` on the Control Node to route `simple-model` tasks (e.g., tool execution) to small, fast models on the K8 Plus, while routing `complex-model` tasks to massive reasoning models (e.g., Llama 4 109B) over the LAN to the EVO-X2.
3. **Hot/Cold Swapping:** Establish logic/timeout protocols within the runners to seamlessly swap specialized models (vision, code) into VRAM when required and evict them when idle.

---

## Phase 1: Safe Execution (Sandboxing)

* **Category:** `services/sandboxes/`
* **Target Providers:** `gVisor` (Local Linux hardening), `E2B` (Cloud ephemeral execution).
* **Purpose:** Move beyond the basic `docker-dood` implementation to prevent malicious or hallucinated agent code from escaping the container namespaces and corrupting the host OS.

## Phase 2: External Interaction (Browsers, Fetchers, and Searchers)

* **Categories:** `services/browsers/`, `services/fetchers/`, `services/searchers/`
* **Purpose:** Expand the Tier 0 demonstration capabilities into robust 24/7 background tasks. Implement visual DOM interpretation (`Skyvern`), action-caching to save API costs (`Stagehand`), and self-healing data extraction that doesn't break when CSS classes change.

## Phase 3: Source Truth & Reliability (VCS & CI)

* **Category:** `services/vcses/` & `services/ci/`
* **Target Providers:** `Forgejo / Gitea`, `Woodpecker CI / Drone`
* **Purpose:** As agents autonomously modify workspace files, we need absolute attribution. CI pipelines will mathematically prove the agent's code works against a test suite before it is deployed.
Note: The `vcses` service currently has no providers implemented and needs initial integrations added.

## Phase 4: Decoupling & Debugging (Queues & Tracing)

* **Category:** `services/queues/` & `services/tracers/`
* **Target Providers:** `RabbitMQ`, `OpenTelemetry + Jaeger / SigNoz`
* **Purpose:** Prevent timeouts during complex multi-agent swarms by decoupling synchronous HTTP calls. Provide deep visibility into latency spans to debug slow agent reasoning loops.

## Phase 5: Secure Public Ingress (Reverse Proxy & IAM)

* **Categories:** `services/proxies-reverse/`, `services/iam/`
* **Target Providers:** `Traefik / Caddy`, `Authelia / Authentik`
* **Purpose:** Expose specific agent endpoints (like a shared public webhook receiver) to external users via strict Multi-Factor Authentication and SSL termination.

---

## Beyond Software: The Hardware Scaling Journey

As users graduate from the entry-level "Tier 0" laptop footprint to distributed "Tier 1" monoliths and "Tier 2+" compute/archive planes, users must evaluate the following architectural challenges:

### 1. Memory and Inference Constraints
* **Unified Memory Allocation:** Given advanced APU architectures (like the Strix Halo in the GMKtec EVO-X2), does the BIOS allow you to explicitly pin a dedicated VRAM allocation for the iGPU? This is critical to prevent the Linux kernel from reclaiming memory during heavy LLM inference.
* **Thermal Throttling:** Are there thermal or acoustic constraints for running high-TDP nodes 24/7 in a residential or nomadic environment?

### 2. Network Topology & Latency
* **Context Window Transfers:** How will you handle the physical network topology to ensure the 2.5GbE interfaces on the GMKtec nodes communicate with future 10GbE nodes without introducing switch latency during massive 100k+ context window transfers? (A Star Topology via a multi-gigabit core switch is mandatory).
* **Subnet Routing:** How will Tailscale subnet routing be configured to ensure external webhooks reach the Gateway seamlessly when physical nodes change networks during travel?

### 3. Distributed Storage & Persistence
* **State Synchronization:** How will you manage distributed storage persistence and backups across multiple ephemeral nodes?
