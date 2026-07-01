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

### The "Zero Straight-Jacket" Principle
Meta<Claw> is explicitly designed to be unobtrusive and un-opinionated. Previous
iterations required aggressive workarounds, monkey-patches, and strict
architectural straight-jackets to force the ecosystem to function safely. As
OpenClaw has matured (2026.6.8+), Meta<Claw> has shed this cruft.

Our primary directive is to provide a seamless, robust provisioning pipeline
that sets up the ecosystem for non-technical users and then **gets completely
out of the way**. We make it incredibly easy to get up and running, but we do
not put users in a straight-jacket. The framework does not dictate your agent
logic, your prompt structures, or your internal UI configurations.

### The 4 Functional Hardware Planes

To successfully deploy the ecosystem, the services defined in `SERVICES.md` are
logically (and eventually physically) isolated into four hardware Planes based
on their resource utilization profiles and security trust levels.

**THE MESH INVARIANT (OPTIONAL):** If you require remote access outside of your
home LAN, **Overlay Networks (e.g., Tailscale)** must run across ALL hardware
nodes concurrently. They provide the foundational `100.x.y.z` zero-trust mesh
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
format in `./docs/SERVICES.md`.

### Decoupling Tiers from Planes

Meta<Claw> draws a strict architectural distinction between a "Tier" and a "Plane".
* **A Plane** is a logical, functional role (Control, Compute, Execution, Archive).
* **A Tier** does not represent a single computer. A Tier represents a discrete stage in the growth of your overall local cluster. A single node within a cluster hosts one or more Planes.

* Many users will start at **Tier 0**, some will jump right to **Tier 1**, and
    many will decide not to go any further, content to use cloud-based LLMs and
    surviving within the constrained footprints provided by Tiers 0 and 1.
* Some users will explore Tiers 2, 3 and 4 (which can occur in any order and
    independent of one another).
* **Tier 2** advances the cluster by adding a dedicated Compute Node (or nodes)
    for local LLM inference, moving that workload off the Control node to avoid
    cloud-based API Keys and bills.
* **Tier 3** advances the cluster by adding a dedicated Execution Node, whose
    hardware is heavily optimized for sandboxing and volatile CI workloads.
* **Tier 4** advances the cluster by adding a dedicated Archive Node, whose
    hardware (ECC RAM, high-IOPS NVMe arrays) is explicitly optimized to host
    massive vector databases and observability telemetry.
* **Tier 5** introduces an edge computer for allowing a user to share some of
    their compute resources with other users (Future Roadmap).

## Remote Access & The Headless Invariant

Because most of the services must be co-located on a high-speed LAN, users who
travel (e.g., via Starlink) face a connectivity challenge. Meta<Claw> relies on Tailscale deployed directly on the host operating systems of all cluster nodes.

**THE HEADLESS LIFELINE INVARIANT:**
When deploying to a headless Linux node (accessed exclusively via SSH), Tailscale **MUST** be run natively on the bare-metal OS (`"metal": true`). It is strictly forbidden to run Tailscale within a Docker container on a headless node.
If Tailscale is containerized, any framework reset (e.g., `make factory-reset-soft` calling `docker compose down`) will destroy the mesh interface, sever the user's SSH tunnel, and permanently lock them out of the remote machine. MetaClaw's orchestrator natively detects bare-metal lifelines and excludes them from teardown loops.

## Software Design Decisions

### Ephemeral Gateway State (Cattle, not Pets)

Standard OpenClaw installations treat `~/.openclaw` as a "pet"—something to be kept alive, updated, and carefully maintained across versions. MetaClaw treats the OpenClaw Gateway as "cattle"—ephemeral compute that can be destroyed and rebuilt instantly.

During a `factory-reset-soft`, the entire `config/openclaw.json` state is wiped.
* **The Benefit:** Wiping the JSON guarantees zero configuration drift between framework updates, ensuring a sterile, perfect boot sequence. It enforces an "Immutable Infrastructure" mindset, forcing users to define their agents natively in `.yaml` workspace files rather than relying on brittle UI state.
* **The Tradeoff:** Wiping the config deletes the browser's pairing state. To mitigate this, MetaClaw implements an `auto_approve.py` background worker that uses schema-aware JSON parsing to seamlessly intercept and approve new Device Identities the moment a user opens the GUI, ensuring the user experience remains frictionless.

### Centralized Service Discovery & Network Aliasing

To ensure services can be swapped instantly or migrated across hardware without
breaking downstream dependencies, we enforce strict network aliasing and
centralized configuration.

* **State Synchronization & Distributed DNS:** Migration between hardware tiers
    relies on a shared `profile.json` file. As you add new nodes to the cluster,
    the `bin/orchestrate.py` script automatically generates a `.env.cluster` file
    containing dynamic variables (e.g., `ACTIVE_RUNNER_HOST=192.168.1.50`). This
    allows services on the Control Plane to seamlessly discover other services that
    have migrated to new hardware nodes.
* **`active-proxy`:** Whether running LiteLLM, Helicone, or a custom router,
    the proxy container MUST alias itself on the Docker network as `active-proxy`.
    Downstream services connect blindly to `http://active-proxy:4000`.
* **`active-memory`:** The database container (PostgreSQL, Qdrant, etc.) MUST
    alias itself as `active-memory`.

### Service Segregation

The framework is strictly delineated into modular services, each with their own
directory hierarchy (see `SERVICES.md`). Mixing concerns (e.g., placing
Observability tools inside the Sandbox service) is forbidden.

### The Symlink Context Invariant
Meta<Claw> relies heavily on symlinks within the `services/` directory (e.g.,
`services/proxy` -> `services/proxies/litellm`).

**CRITICAL INVARIANT:** Whenever executing commands (especially `make` or `docker compose`)
against a service, automation scripts MUST resolve the symlink to its physical path
(using `readlink` or `os.path.realpath()`).

If Docker Compose is executed from within a logical symlink path, it evaluates
relative paths (like `- ../../memory/.env`) based on the symlink's location,
resulting in missing files, silent failures, and orphaned containers during teardown.
The MetaClaw root `Makefile` and `bin/orchestrate.py` strictly enforce physical path resolution.

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
