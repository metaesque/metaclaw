# OpenClaw Framework: Service Expansion Roadmap

*Note: With the upgrade to OpenClaw 2026.6.8, Meta<Claw> has formally adopted an "un-opinionated" design goal. We aim to make it incredibly easy for non-technical users to get OpenClaw running, without placing them in a straight-jacket once the environment is operational. All future roadmap items are evaluated against this ethos.*

This document outlines the prioritized architectural strategy for integrating future software capabilities.

*(Semantic Note: The "Phases" below refer exclusively to software capability rollouts. The hardware scaling progression is referred to as "Hardware Tiers". See the Hardware Scaling section at the bottom of this document for critical infrastructure questions.)*

---

## 🎯 IMMEDIATE MILESTONE 1: The Tier 0 Demonstration Gallery

**Urgency: HIGH**

**The Goal:** Prove the concrete utility of MetaClaw's complex service architecture to non-technical users by providing pre-configured "Example Agents" that tangibly benefit from the installed providers.

**Demonstration Use-Cases to Implement:**
1.  **The "Live Researcher" Agent:** Demonstrates the `searxng` and `jinareader` (Tier 0 Fetchers/Searchers). When asked about a software library released yesterday, the agent autonomously searches the web, fetches the live documentation, parses the markdown, and answers accurately, proving it is no longer bound by its stale training data.
2.  **The "Long-Term Colleague" Agent:** Demonstrates `postgres/pgvector` (Memory). The agent recalls minor personal details (like hardware specs or preferred coding styles) established weeks prior across dozens of disconnected chat sessions via semantic RAG.
3.  **The "Autonomous Coder" Agent:** Demonstrates `docker-dood` (Sandbox). Instead of just printing Python code in a chat block, the agent silently spins up an ephemeral container, executes the script, captures a `SyntaxError`, fixes its own code, runs it again, and only replies to the user once the code executes successfully.

## 🎯 IMMEDIATE MILESTONE 2: The Tier 2 Linux Migration

**Urgency: HIGH**

**The Goal:** Graduate from the constrained Tier 0 laptop and deploy the framework onto dedicated edge hardware (GMKtec K8 Plus as the Tier 1 Control/Archive Monolith, and GMKtec EVO-X2 as the Tier 2 Compute node).

**Critical Path:**
1. **Physical Provisioning:** Install Ubuntu Server 24.04 LTS, pin the EVO-X2 BIOS VRAM allocation for the Strix Halo APU, and establish the Tailscale mesh.
2. **AMD Inference Optimization:** Patch the `ollama` provider to support ROCm/Vulkan device passthrough (`/dev/kfd`, `/dev/dri`) to utilize the EVO-X2's unified memory.
3. **Execution Plane Upgrades:** Implement Linux-native, 24/7 background providers: `stagehand` (Browsers), `scrapegraphai` (Fetchers), and `exa` (Searchers).

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
* **Purpose:** As agents autonomously modify workspace files, we need absolute attribution. CI pipelines will mathematically prove the agent's code works against a test suite before it is deployed. Note: The `vcses` service currently has no providers implemented and needs initial integrations added.

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
