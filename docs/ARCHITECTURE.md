# Meta<Claw> Architecture Manifesto

This document defines the strict engineering invariants, hardware scaling
strategies, and prompt routing philosophies for Meta<Claw>. It serves as the
single source of truth for the system's design decisions.

*Note for AI Contributors: Strict instructions regarding codebase modification,
epistemic boundaries, and output formatting have been relocated to
`docs/LLM.md`. You must review that file before proposing structural changes.*

## Core Hardware Philosophy: Incremental Expansion

The OpenClaw Infrastructure Framework is designed to solve the primary adoption
barrier for autonomous AI agents: the immense initial hardware overhead. The
framework is built on a philosophy of **"Incremental Expansion without Hardware
Waste."**

Non-technical users are not required to build a distributed data center on Day
1. Instead, the architecture allows users to validate the utility of personal AI
agents on their existing dual-use laptops. As their reliance on the system
grows, they can incrementally expand into dedicated hardware. Each new hardware
purchase targets a specific functional bottleneck, cleanly taking over a subset
of services without rendering previous hardware obsolete.

### The 4 Functional Hardware Planes

To successfully deploy the ecosystem, the services defined in `SERVICES.md` are
logically (and eventually physically) isolated into four hardware Planes based
on their resource utilization profiles and security trust levels.

**THE MESH INVARIANT (OPTIONAL):** If you require remote access outside of your
home LAN, **Overlay Networks (e.g., Tailscale)** must run across ALL hardware
tiers concurrently. They provide the foundational `100.x.y.z` zero-trust mesh
network that allows these distinct tiers to securely discover and communicate
with each other over the WAN, bypassing Carrier-Grade NAT (CGNAT) and firewalls.
If you strictly operate on a single home LAN, this service is unnecessary.

**CRITICAL LATENCY INVARIANT:** The Control, Context, and Execution Planes
**MUST** reside on the same physical Local Area Network (LAN). Vector database
queries (Context) require sub-millisecond retrieval latency. Browser automation
(Execution) pushes massive amounts of DOM data back to the Gateway. While the
Compute Plane (LLM Runner) *can* technically be remote, uploading massive
100k-token prompt contexts over an asymmetrical WAN will induce multi-second
delays before inference begins. For a fluid agent experience, the entire farm
should reside on the same gigabit LAN.

The planes are formalized in `./planes.json` and available in human-readable
format in `./docs/STRUCTURE.md`.

### The 5 Phases of the Hardware Journey

Meta<Claw> identifies a 5-phase hardware journey that users may take.
* Many users will start at Phase 0, some will jump right to Phase 1, and many will
  decide not to go any further, content to use cloud-based LLMs and surviving
  within the constrained footprints provided by Phases 0 and 1.
* Some users will explore Phases 2, 3 and 4 (which can occur in any order and
  independent of one another).
* Phase 2 provides local LLM compute (avoiding cloud-based API Keys and bills)
* Phase 3 moves the Execution Plane from the Phase 1 computer to a dedicated
  computer whose hardware is especially suited to the services in the
  Execution Plane.
* Phase 4 moves the Archive Plane from the Phase 1 computer to a dedicated
  computer whose hardware is especially suited to the services in the
  Archive Plane.
* Phase 5 introduces an edge computer for allowing a user to share some of
  their compute resources with other users.

The phases are formalized in `./phases.json` and available in human-readable
format in `./docs/STRUCTURE.md`.

## Remote Access

Because most of the services must be co-located on a high-speed LAN, users who
travel (e.g., via Starlink) face a connectivity challenge.

* **The Zero-Trust Overlay (Tailscale):** Meta<Claw> relies on Tailscale (a
  zero-configuration WireGuard mesh network) deployed directly on the host
  operating systems of all cluster nodes.

* **Mechanics:** Tailscale assigns a static, private `100.x.y.z` IP to every
  node in the homebase cluster and to the nomad's travel laptop.

* **Result:** The user accesses the OpenClaw Dashboard remotely via
  `http://100.x.y.z:18789`. Furthermore, the user can utilize `tailscale ssh`
  to securely jump into any node in the farm to execute `make` targets from
  anywhere in the world, entirely bypassing the public internet without exposing
  sensitive GUI ports.

## Software Design Decisions

### Centralized Service Discovery & Network Aliasing

To ensure services can be swapped instantly or migrated across hardware without
breaking downstream dependencies, we enforce strict network aliasing and
centralized configuration.

* **State Synchronization & Distributed DNS:** Migration between hardware phases
  relies on a shared `profile.json` file. As you add new nodes to the cluster,
  the `bin/orchestrate.py` script automatically generates a `.env.cluster` file
  containing dynamic variables (e.g., `ACTIVE_RUNNER_HOST=192.168.1.50`). This
  allows services on the Control Plane to seamlessly discover other services that
  have migrated to Phase 2 or Phase 3 nodes.

* **`active-proxy`:** Whether running LiteLLM, Helicone, or a custom router,
  the proxy container MUST alias itself on the Docker network as `active-proxy`.
  Downstream services connect blindly to `http://active-proxy:4000`.

* **`active-memory`:** The database container (PostgreSQL, Qdrant, etc.) MUST
  alias itself as `active-memory`.

### Service Segregation

The framework is strictly delineated into modular services, each with their own
directory hierachy (see `SERVICES.md`). Mixing concerns (e.g., placing
Observability tools inside the Sandbox service) is forbidden.

## Prompt-to-Model Routing

Ensuring that the right AI model is used for each prompt is critical. "Right" is
defined as the most cost-effective model capable of providing an exceptional
answer. The routing process is divided into 5 distinct strategies that cascade
progressively.

1.  **Deterministic Routing (Pre-cognitive):** Hardcoded, strict 1:1 mapping
    based on system state, tool selection, or explicit user overrides,
    completely independent of the prompt's semantic content.
2.  **Lexical Routing (Heuristic / Fast-Path):** Analyzes raw text for reasoning
    markers (e.g., "think step by step"), structural complexity (JSON schemas),
    code presence, or simple commands (e.g., `heartbeat`). Trivial commands are
    routed immediately to local/cheap models.
3.  **Semantic Routing (Vector Similarity):** Uses a fast embedding model to map
    the prompt to a vector space, comparing it against a database of known
    "simple" or "complex" queries to determine routing.
4.  **Predictive Routing (LLM-as-a-Judge):** A micro-model (often quantized
    locally) reads the prompt and outputs a discrete complexity score (`simple`,
    `medium`, `complex`, `reasoning`) before the primary inference occurs. The
    prompt is then directed to the corresponding proxy tier.
5.  **Fallback Routing (Reactive Cascading):** A trial-and-error approach. If a
    low-tier model fails a validation check (e.g., broken JSON or timeout), the
    system automatically retries with a high-tier model.

## Context Compaction Safeguards

Agents are highly susceptible to "Context Bloat." In long-running sessions,
appending full file contents and history can push prompts past 20,000+ tokens,
driving up costs and inducing extreme latency.

* **The Invariant:** All agent default profiles MUST be patched with a strict
  `compaction` threshold policy.

* **The Mechanism:** When a session exceeds the `reserveTokensFloor` (e.g.,
  24,000 tokens), the Gateway invokes a cheaper model (e.g.,
  `litellm/medium-model`) to summarize the history and squash the context window
  back down. This preserves the bandwidth of the expensive, high-tier models
  strictly for reasoning tasks rather than reading ancient history.
