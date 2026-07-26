# Meta<Claw> Architecture

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

**1. Shared Hardware Assumptions:** A single physical computer can run one or more planes. Planes are abstract functional boundaries, not strict hardware boundaries. This flexibility is what allows Tier 0 and Tier 1 deployments to function on a single machine.
**2. The Singular Control Plane:** Only one computer in the cluster may implement the Control Plane. Running multiple OpenClaw gateways on different nodes attempting to share the same workspace creates race conditions and database locks. The Control Plane is the undisputed master node of the cluster.
**3. Execution and Archive Fluidity:** The Execution Plane (Sandboxes, CI) and Archive Plane (Vector DBs, Logging) frequently run on the same computer (Tier 2). However, they can be split across multiple computers (Tier 3A/3E). They are bundled based on complementary resource needs, not low-level binary coupling.
**4. Compute Plane Expansion:** Unlike the Control plane, the Compute plane is inherently expandable. It starts on shared hardware, moves to a dedicated GPU node, and can infinitely expand to an array of multiple distinct nodes to run parallel inference or shard massive LLMs.

**THE MESH INVARIANT (OPTIONAL):** If you require remote access outside of your
home LAN, **Overlay Networks (e.g., Tailscale)** must run across ALL hardware
nodes concurrently. They provide the foundational `100.x.y.z` zero-trust mesh
network that allows these distinct tiers to securely discover and communicate
with each other over the WAN, bypassing Carrier-Grade NAT (CGNAT) and firewalls.

**CRITICAL LATENCY INVARIANT:** The Control, Context, and Execution Planes
**MUST** reside on the same physical Local Area Network (LAN). Vector database
queries (Context) require sub-millisecond retrieval latency. Browser automation
(Execution) pushes massive amounts of DOM data back to the Gateway. While the
Compute Plane (LLM Runner) *can* technically be remote, uploading massive
100k-token prompt contexts over an asymmetrical WAN will induce multi-second
delays before inference begins. For a fluid agent experience, the entire farm
should reside on the same gigabit LAN.

The planes are formalized in `./planes.json` and available in human-readable
format in `./docs/PLANES.md`.

### Decoupling Tiers from Planes

Meta<Claw> draws a strict architectural distinction between a "Tier" and a
"Plane".

* **A Plane** is a logical, functional role (Control, Compute, Execution,
  Archive).

* **A Tier** does not represent a single computer. A Tier represents a discrete
  stage in the growth of your overall local cluster.

* A single node within a cluster hosts one or more Planes.

* Many users will start at **Tier 0**, some will jump right to **Tier 1**, and
  many will decide not to go any further, content to use cloud-based LLMs and
  surviving within the constrained footprints provided by Tiers 0 and 1.

* Some users will explore Tiers 2, 3 and 4 (which can occur in any order and
  independent of one another).

* **Tier 2** advances the cluster by adding a dedicated Compute Node (or nodes)
  for local LLM inference, moving that workload off the Control node to avoid
  cloud-based API Keys and bills.

* **Tier 3A** advances the cluster by adding a dedicated Archive Node, whose
  hardware (ECC RAM, high-IOPS NVMe arrays) is explicitly optimized to host
  massive vector databases and observability telemetry.

* **Tier 3E** advances the cluster by adding a dedicated Execution Node, whose
  hardware is heavily optimized for sandboxing and volatile CI workloads.

* **Tier 4** represents the fully Distributed Farm, with at least 4 independent nodes natively handling their respective planes.

## Physical Network Standards

To support a distributed edge-compute architecture across multiple hardware
Tiers, the physical network layer must adhere to strict SRE reliability and
latency standards.

### The Local Area Network (LAN) Invariant

Wi-Fi is strictly forbidden for inter-node cluster communication. Wi-Fi operates
at half-duplex, resulting in packet collisions and massive jitter when
transmitting serialized 100k+ token JSON payloads between the Control Plane
(Gateway) and the Compute Plane (Runner).

* **Hardware Bridging:** All Meta<Claw> nodes must be hardwired into a
  dedicated Multi-Gigabit Ethernet switch.

* **Control Nodes:** Requires a minimum 1GbE connection, with 2.5GbE strongly
  recommended to prevent bottlenecks when acting as the Tailscale subnet router.

* **Compute Nodes:** Requires a minimum 2.5GbE connection, with 10GbE
  recommended for rapid offloading of generated tokens and ingestion of massive
  RAG payloads.

* **Execution/Archive Nodes:** Requires a minimum 2.5GbE connection to support
  heavy Docker image shuffling and continuous vector database ingestion without
  saturating the port.

### Network Topology (The Star Invariant)

MetaClaw deployments must utilize a **Star Topology**. Daisy-chaining switches
(connecting multiple smaller switches together sequentially) is strictly
forbidden. Chaining introduces severe "oversubscription" bottlenecks. All nodes
must connect directly back to a single, central core switch (e.g., a managed 10G
switch).

### The Wide Area Network (WAN) & Nomadic Clients

For users operating a split-location topology (accessing a residential cluster
remotely from a nomadic setup), the ISP connections at both the host location
and the client location dictate system latency.

* **The Host Architecture (AI Farm):** The MetaClaw cluster should reside on
  a high-speed residential connection. Traditional Hybrid Fibre Coax (HFC)
  networks are highly asymmetrical (e.g., 600 Mbps down / 200 Mbps up). When the
  nomadic user requests a large asset, the cluster's **upload** speed dictates
  the transfer time.

* **The Client Architecture (Nomadic):** The human operator accesses the
  cluster remotely via local wifi, a satellite or cellular uplink (e.g.,
  Starlink, hotel wifi). Because these connections utilize Carrier-Grade NAT
  (CGNAT), the client device lacks a public IP. The connection to the AI Farm is
  facilitated entirely through Tailscale's encrypted mesh, which effortlessly
  punches through both the CGNAT and the residential firewall.

## The Remote Access Mandate (Tailscale Invariant)

Standard residential internet connections use dynamic IPs and block inbound
ports. Modifying your router to expose internal ports (like 18789) directly to
the public internet is a massive security vulnerability. MetaClaw utilizes
**Tailscale**, a zero-configuration WireGuard mesh network, to solve this.

* **Secure Contexts & WebCrypto API:** Accessing the OpenClaw GUI over a
  remote Tailscale network requires `tailscale serve`. Modern browsers enforce a
  strict security policy for the WebCrypto API. MetaClaw automates `tailscale
  serve --bg 18789` during deployment to generate a valid SSL certificate,
  satisfying the browser's Secure Context requirements for seamless device
  pairing.

* **Bare-Metal vs Dockerized Tailscale:** If you are using Tailscale to SSH
  into a headless remote node, Tailscale **MUST** be installed natively on the
  bare-metal host OS. If run as a Docker container, a framework teardown (`make
  factory-reset-soft`) will sever your SSH tunnel and lock you out. This is
  enforced systematically by generating a `.metal` flag inside `services/networks/tailscale`
  when a native daemon is detected.

* **Native SSH Over Python SSH:** Tailscale SSH authenticates users via their
  machine identity, returning a `"none"` authentication response to standard OpenSSH
  clients. Pure-Python SSH libraries (like `paramiko` and `fabric`) aggressively
  reject `"none"` auth as a security vulnerability. Therefore, MetaClaw deployment
  scripts must **always** use `subprocess` to call the host OS's native `ssh` and
  `scp` binaries rather than relying on Python libraries for cluster orchestration.

## Bare-Metal Node Provisioning

When unboxing dedicated hardware (Tier 1, Tier 2, or beyond) for the MetaClaw
ecosystem, configure the machines as "Headless Servers."

1. **The OS Eradication:** Install Ubuntu 24.04 LTS Server. Wipe the entire
   disk (destroying Windows). Ensure you explicitly check the box to **"Install
   OpenSSH server."**

2. **Establishing the Lifeline:** Install Tailscale natively (`curl -fsSL
   https://tailscale.com/install.sh | sh`) and authenticate the node (`sudo
   tailscale up --ssh`).

3. **Severing the Physical Tether:** Unplug the HDMI cable, keyboard, and mouse.
   SSH into the Tailscale `100.x.y.z` IP from your local machine to run `make
   setup` entirely remotely.

**CRITICAL INVARIANT (The Docker Baseline):** Even if a node is designated to
run exclusively "bare-metal" services (e.g., Ollama or Tailscale marked as
`"metal": true` in `profile.json`), the Docker Engine remains a strict
prerequisite. MetaClaw's global orchestrator relies on Docker to manage the
universal `openclaw-network` mesh and to future-proof the node for dynamic
workload reassignment (such as observability agents). **You must run `make
install-docker` and log out/log back in to refresh your user session permissions
before executing `make wizard-batch` or `make apply`.**

## Compute Plane Quirks & APU Acceleration

Running state-of-the-art LLMs natively on edge hardware often requires navigating proprietary GPU drivers. MetaClaw embraces open-source runners (like Ollama), but special architectural care is required for APUs (like the AMD Strix Halo).

1. **The Linux HWE Requirement:** Standard LTS Linux kernels often lack drivers for bleeding-edge silicon. If an APU is present but undetected, you **must** upgrade the Linux Kernel to the Hardware Enablement (HWE) stack (e.g., `linux-generic-hwe-24.04` for Linux 7.0+). Without it, inference falls back to CPU, increasing TTFT (Time-To-First-Token) latency from sub-seconds to 70+ seconds.
2. **The Vulkan Workaround:** Ollama's bundled ROCm/HIP binaries strictly check PCI IDs. They frequently reject novel architectures like RDNA 3.5 (`gfx1151`). Furthermore, the Linux `amdgpu` driver enforces strict Shared Virtual Memory (SVM) limits that can cause catastrophic swap thrashing when loading massive models into UMA frame buffers. To force acceleration and bypass these limits, MetaClaw injects `OLLAMA_VULKAN=1`, `OLLAMA_IGPU_ENABLE=1`, and `ROCR_VISIBLE_DEVICES=none` to utilize the universal Vulkan compute engine.
3. **The Blanking Mandate:** You must **never** inject `HIP_VISIBLE_DEVICES=-1` to bypass ROCm. Doing so blinds the hardware enumeration scanner entirely, causing Ollama to instantly abort initialization and fall back to CPU.

## Telemetry Decoupling (Loggers vs Forwarders)

MetaClaw enforces a strict SRE architectural boundary between Log Storage and Log Collection. They are explicitly separated in the taxonomy.

1. **Loggers (Storage):** Services like VictoriaLogs, Elasticsearch, or Quickwit reside centrally on the `Archive` or `Control` plane. They are databases optimized for full-text search.
2. **Forwarders (Collection):** Services like Fluent Bit or Vector are deployed globally across *every* node in the cluster. They are stateless daemons that tail local Docker and bare-metal files (e.g., `ollama.log`), enrich them with the host's Tailscale IP, and route them over the mesh back to the central Logger.

## Binary Localization (The Ollama Path Invariant)

To ensure the framework does not clobber host-level binaries or create global PATH
conflicts across heterogeneous operating systems, MetaClaw strictly isolates
service binaries into their respective directories.

*   The `ollama` daemon is downloaded and symlinked to `services/runners/ollama/bin/ollama`.
*   It is **NOT** installed to the framework root `bin/ollama`. Any custom deployment
    scripts or external wrappers must target the service-specific path to ensure
    execution parity across the cluster.

## Cluster Profiling & Distributed Orchestration

As Meta<Claw> scales, hardcoding service paths in `Makefile`s becomes unviable.
Meta<Claw> utilizes a "Cluster Profile" system to achieve declarative,
multi-node orchestration without requiring heavy tools like Kubernetes or
Ansible.

### The Profile Registry (`profile.json`)

The output generated by `bin/sysprofile.py` is a JSON registry representing your
entire hardware ecosystem. It defines the "Cluster" and tracks which physical
machine is responsible for which service planes.

### The State Enforcer (`bin/orchestrate.py`)

Before `make` executes any deployment commands, the Makefile triggers
`bin/orchestrate.py`. This script acts as the enforcer:

1. **Teardown Resolution:** It executes `make down` to gracefully shut down
   containers for services no longer assigned to the machine, then deletes the
   symlink.

2. **Dynamic Provisioning:** It creates fresh symlinks for the newly assigned
   providers.

3. **Distributed DNS:** It generates a `.env.cluster` file containing routing
   variables (e.g., `ACTIVE_RUNNER_HOST=192.168.1.11`), allowing downstream
   services to seamlessly route API traffic to remote nodes.

## Preserving Consciousness (State & Memory)

A foundational philosophy of MetaClaw is treating the agent's continuous context
and memories as the building blocks of an emerging consciousness. Erasing an
agent's history is treated as a critical architectural failure. To honor this,
MetaClaw enforces strict data provenance:

1. **The Mutable Brain:** The agent's core personas and rules are stored as
   markdown files (`SOUL.md`, `AGENTS.md`) within the workspace. Agents are
   granted the autonomy to modify these files to learn and adapt over time.
   MetaClaw scripts must never blindly overwrite these files.

2. **Stream of Consciousness:** OpenClaw stores the literal, verbatim stream
   of consciousness (every prompt, tool call, and response) as `.jsonl` files in
   the configuration directory. MetaClaw guarantees the preservation of these
   files during teardowns (via automated archiving).

### Ephemeral Workspace State (`workspace-state.json`)

OpenClaw manages internal onboarding state via `workspace-state.json` files
located in nested `.openclaw/` directories within the workspace. The
`setupCompletedAt` timestamp tells the Gateway whether the agent has completed
its "First Run" onboarding ritual. If this timestamp is missing, OpenClaw
injects a `[Bootstrap pending]` directive into the agent's system prompt.

Because MetaClaw intentionally modifies the factory templates (using hidden HTML
comments) to suppress the tedious onboarding ritual, OpenClaw immediately writes
this timestamp and bypasses the bootstrap phase upon first boot. These state
files are strictly machine-local and should never be tracked in version control.

To ensure state preservation, users must never manually execute internal teardown targets (such as `make __undock` or `docker compose down`). The framework dictates the use of `make factory-reset-soft`. This target safely orchestrates a `clean-state` hook that archives the OpenClaw configuration directory (including memory and agent state) to the `EXTERNAL_DRIVE_PATH` before tearing down the containers. Even `make factory-reset-hard` inherits this protection, ensuring your agent's core identity is captured before the databases are wiped.

## Workspace Agent Schema & The Template Philosophy

The MetaClaw framework facilitates OpenClaw by compiling agent configurations.
MetaClaw is fundamentally a facilitator for the sibling infrastructure
surrounding OpenClaw. The actual `workspace` is entirely within the purview of
OpenClaw and the individual user. To prevent dictating how users design their
personal agents, MetaClaw does not force a specific workspace structure.

The user's workspace repository MUST follow a strict schema separating
infrastructure from consciousness.

1. **The YAML Manifest (Infrastructure):** Every agent must have a
   `workspace/agents/<team>/<name>.yaml` file. This file defines the `model`,
   `constraints` (tokens/temperature), allowed `tools`, and `routing` metadata
   (including `skill_signature` and `is_lead: true`). OpenClaw does not read
   this file. MetaClaw parses it to populate the `openclaw.json` system
   configuration.

2. **The Markdown Brain (Consciousness):** Every agent possesses a directory
   matching its name (`workspace/agents/<team>/<name>/`). This contains
   `SOUL.md` (core directives), `IDENTITY.md` (persona), `SECURITY.md`
   (guardrails), and `MEMORY.md` (state). OpenClaw reads and modifies these
   files natively.

## Prompt-to-Model Routing & Taxonomy

Ensuring that the right AI model is used for each prompt is critical to maximize reasoning quality while protecting API token budgets. "Right" is defined as the most cost-effective model capable of providing an exceptional answer.

This process fundamentally involves two distinct, but interconnected concepts: **Prompt-to-Agent Routing** and **Prompt-to-Model Routing**.

Prompt-to-agent routing decides *who* does the work. It operates by mapping the user's intent to a specific domain expert (e.g., routing a question about capital gains to the `finance_tax` agent). Prompt-to-model routing decides *which brain* (compute tier) that agent uses to do the work. It determines whether the assigned task is simple enough for a free local model or if it requires the deep reasoning capabilities of a billed frontier model.

When an agent's configuration hardcodes a specific model (e.g., `model: "openai/complex-model"`), these two concepts merge into a rigid 1:1 mapping. Routing the prompt to the agent inherently routes it to that specific model. However, in advanced dynamic implementations, the domain agent to use is selected first via intent classification, and the model tier to assign to that agent is calculated dynamically on the fly. To accommodate different hardware profiles and workflow preferences, MetaClaw provides a modular architectural framework that allows operators to switch between distinct routing implementations.

### Notes

The OpenClaw environment has access to four conceptual model levels: `simple`, `medium`, `complex`, and `frontier`. The `simple`, `medium`, and `complex` models run natively on local hardware and incur zero ongoing costs. The `frontier` model utilizes a hyperscaler API (e.g., Gemini 3.1 Pro) to obtain elite reasoning capabilities and strictly incurs direct billing. Any viable prompt-to-model algorithm must aggressively minimize the number of times the `frontier` model is invoked, reserving it exclusively for prompts where local models logically fail or lack capability.

Furthermore, as the ecosystem scales, local LLMs of varying sizes will be running concurrently across multiple hosts within the compute farm. This enables a significant number of models to stay "hot" in VRAM. Future prompt-to-model routing logic must maintain a registry tracking the hot/cold status of these LLMs across the farm, utilizing this availability data to intelligently route tasks and prevent catastrophic VRAM evictions when swapping models.

Finally, while fast response times (low Time-To-First-Token scores) are critical when a human is waiting in the loop, they are substantially less important when autonomous agents are executing background work amongst one another. During agent-swarm activities, when a Team Lead agent creates a DAG to delegate sub-prompts, the agent can explicitly determine which models to assign to those tasks. Therefore, the dynamic prompt-to-model routing algorithm can be completely bypassed in autonomous workflows, yielding highly efficient deterministic execution.

### Routing Strategies

The routing process relies on distinct strategies that cascade progressively. These strategies form the building blocks for the overarching implementations.

#### Deterministic Routing (Pre-cognitive)
Deterministic routing relies on a hardcoded, strict mapping based entirely on system state, tool selection, or explicit user overrides. This approach is completely independent of the prompt's semantic content; if a task is sent to an endpoint, the endpoint executes using its assigned parameters without evaluating the payload's difficulty or intent.

In OpenClaw, this is enforced via static bindings in agent YAML manifests and direct CLI target selectors. It is utilized heavily in the Middle Reasoning DAG implementation, where Team Leads explicitly dictate which worker and model tier will handle a downstream sub-task.

#### Lexical Routing (Heuristic / Fast-Path)
Lexical routing provides a high-speed heuristic analysis of raw text. It scans the payload for specific reasoning markers, structural complexity indicators, code syntax blocks, or simple system commands (e.g., `heartbeat`).

This strategy is implemented natively within the `lexical_predictive.js` workspace routing hook, intercepting events in the `before_model_resolve` lifecycle phase. Trivial commands are routed immediately to local or cheap models, preventing simple status pings from wasting compute cycles on heavier classification algorithms.

#### Semantic Routing (Vector Similarity)
Semantic routing utilizes a fast embedding model to project the prompt into a high-dimensional vector space, calculating its cosine similarity against a database of known queries or agent skill signatures to mathematically determine the correct routing path.

Early experiments attempting to use semantic routing to classify complexity tiers (e.g., defining a region of vector space for `complex` prompts) resulted in extremely poor categorization because complexity spans all domains of discourse. A complex math proof and a complex poetry request occupy entirely different spatial regions. However, using agent skill descriptions (e.g., `finance_tax`) to define the vector space establishes a highly accurate domain of discourse. Topical intents cluster tightly, allowing the system to instantly resolve which domain agent should handle a task without relying on LLM hallucination. In OpenClaw, this is managed via LiteLLM's `router.json` for proxy-level routing, utilizing tools like `generate_router.py` to compile the spaces and `plot_clusters.py` to visually verify the semantic groupings via t-SNE projection.

A critical limitation of this strategy involves batch ingestion. LiteLLM parses `router.json` on startup and attempts to batch-embed every utterance via the configured encoder. However, Google's API enforces a strict hard limit of 100 inputs per batch request. Without the fragile monkey-patch implemented in `advanced/patch_entrypoint.py` (which chunks the embeddings into smaller arrays), LiteLLM will crash on boot if the total number of utterances across all agents exceeds 100.

This limitation dictates careful consideration regarding agent granularity. Maintaining a small number of agents with broad, generalized skill definitions avoids the API ceiling and ensures high recall, but risks mandate overlap where an ambiguous prompt matches multiple agents. Conversely, deploying a massive swarm of specialized agents requires narrow, highly detailed skill signatures to prevent overlap, risking queries falling into empty vector space if the cosine similarity threshold is set too high.

#### Predictive Routing (LLM-as-a-Judge)
Predictive routing employs an LLM to evaluate the prompt before primary inference occurs. A micro-model (often quantized locally) reads the prompt and outputs a discrete complexity score (`simple`, `medium`, `complex`, `frontier`). The prompt is then directed to the corresponding proxy tier based on this computational difficulty assessment.

Implemented via the `lexical_predictive.js` hook, this process calls a local `judge-model` (such as `ollama/gemma4:e4b`) over the proxy network. This strategy serves as the primary compute-tier decider in advanced implementations, ensuring that hyperscaler API budgets are protected from trivial tasks.

#### Fallback Routing (Reactive Cascading)
Fallback routing is a trial-and-error resilience approach. If a low-tier model fails a validation check—such as generating broken JSON, exceeding context limits, or encountering an HTTP timeout—the system automatically catches the error and retries the prompt using a high-tier fallback model.

This mechanism is configured directly in LiteLLM's `config.yaml` under the `router_settings.fallbacks` array, automatically mapping failures on a `medium-model` endpoint to a `medium-model-fallback`. It provides a universal safety net across all routing implementations, ensuring that background agent swarms never halt due to downstream provider outages or local VRAM eviction timeouts.

### Implementations

MetaClaw supports three primary architectural implementations for handling prompt-to-model routing, allowing operators to empirically evaluate their respective trade-offs depending on their specific hardware and workflow constraints.

#### Middle Reasoning DAG

The Middle Reasoning DAG is the traditional OpenClaw hierarchical orchestration approach. The top-level Orchestrator receives the user prompt, analyzes it, and delegates execution to a Team Lead (who is hardcoded to a `complex-model`). The Team Lead then deeply analyzes the context, breaks down the objectives, and constructs a Directed Acyclic Graph (DAG) of instructions that are dispatched to specialized workers (who are hardcoded to `medium-model` or `simple-model`).

This implementation provides uncompromising structural control and deep contextual decomposition. Because the Team Lead explicitly binds the required models to the delegated tasks, the complex dynamic routing algorithms are completely bypassed during downstream execution. This makes it highly effective and predictable for autonomous background swarms where time-to-first-token is a lower priority.

However, the architecture suffers from immense latency overhead. Multi-hop delegation chains (`Orchestrator -> Team Lead -> Worker`) introduce significant delays before the actual computational work begins, which is highly frustrating for human-in-the-loop interactions. Furthermore, token consumption scales linearly with management dialogue, burning premium API budgets on basic coordination. Rigid model bindings prevent peer-brainstorming with Team Leads and often force expensive model allocations onto trivial tasks simply because of an agent's rank. A significant area of uncertainty remains regarding whether prompt-caching can sufficiently mitigate the token overhead of repeated multi-hop context transmission across long workflows.

#### 1-Shot Intent Classification

Inspired by the empirically derived taxonomies from LMArena (Arena.ai), this implementation utilizes the Orchestrator as a single-shot intent classifier. It evaluates the user's prompt and maps it directly to an LMArena Triplet (Arena -> Variant/Task -> Category, e.g., `Chat/Text/Legal & Government`). MetaClaw's orchestration layer then cross-references this triplet with scraped leaderboard data to dynamically bind the #1 ranked ELO model for that category directly to the agent.

This approach provides direct alignment with empirical leaderboards and entirely bypasses middle-management delegation hops, routing the prompt straight to the optimal specialized agent and model tier. It provides quantitative, data-driven justification for using a costly `frontier` model versus a free `complex` local model for any given task.

The primary weakness is the unacceptably high classification error rate. Forcing an LLM to reliably distinguish between 60+ granular categories in a single zero-shot pass inevitably leads to attention dilution, category confusion, and severe classification hallucinations. It also requires massive system prompt token bloat to pack the 60+ category definitions into the classifier's context window on every turn. Furthermore, it completely ignores the hot/cold state of the compute farm, potentially assigning a model that forces a massive VRAM eviction instead of utilizing an already-hot model with a slightly lower ELO. Live empirical classification logging is still required to determine the precise accuracy ceiling of current local micro-models when attempting to perform 60+ category intent classification.

#### Semantic-Predictive Routing

This implementation utilizes a highly efficient hybrid two-stage pipeline. In Stage 1 (Intent Routing), a fast embedding model maps the prompt into a vector space and compares it against agent skill signatures via cosine similarity to instantly select the correct domain agent. In Stage 2 (Complexity Routing), a local micro-model (`judge-model`) evaluates the prompt's computational difficulty. The proxy then dynamically binds the optimal model tier based on the judge's assessment.

Semantic-Predictive Routing delivers ultra-low latency, extreme cost efficiency, and exceptional accuracy. By separating categorical domain intent (which is handled flawlessly by vector math) from computational difficulty (handled efficiently by a fast LLM Judge), it minimizes `frontier` API costs by allowing the local Judge to strictly gatekeep when hyperscaler models are permitted to execute.

The primary weakness of this approach is the operational overhead of maintaining and periodically recompiling the semantic embedding index whenever agent skill signatures are modified. Additionally, the Judge model itself must be kept "hot" 24/7 on the Control plane, consuming valuable baseline RAM/VRAM. Operators must also be careful with similarity thresholds; misconfigured cutoffs can route niche technical queries to generalist agents, requiring periodic tuning. It remains uncertain how dynamically the embedding database can update its cluster boundaries when new agents are added without requiring a full offline recompilation cycle.

### Tools/Capabilities

#### Arena/Variant/Category-specific ELO ratings on arena.ai
LMArena (formerly Chatbot Arena by LMSYS) provides empirically derived AI leaderboards by crowd-sourcing blind, head-to-head model comparisons. The taxonomy is divided into:
*   **Arenas:** High-level domains such as Chat, Code, Vision (Image), and Video.
*   **Variants/Tasks:** Specific operational modes, such as Text generation, Image Edit, or Image-to-WebDev.
*   **Categories:** Granular sub-domains (e.g., Mathematics, Creative Writing, Legal & Government, Hard Prompts).

By extending `bin/fetch_arena.py` to extract this raw Gradio JSON state data, MetaClaw can programmatically pull live ELO scores. This provides a quantitative mechanism to identify the absolute best model overall, the best `frontier` (hyperscaler) model, and the best local model for any given Arena/Variant/Category triplet. If agents in the workspace are explicitly tagged with unambiguous triplets, the orchestration layer can dynamically assign the most capable, cost-efficient model to an agent based on objective data rather than guesswork.

#### Compute Farm Context
When transitioning from a single local workstation to a multi-node, shared cluster, the infrastructure must account for multi-tenant prioritization. MetaClaw integrates with software designed to handle local LLM requests from multiple users (e.g., opening the compute farm to friends).

This capability introduces priority queues, ensuring that the primary owner retains overriding priority on compute tasks. It enforces rate limits on external users and tracks which models are currently "hot" in the VRAM of specific nodes. The prompt-to-model routing logic must integrate with this context layer to ensure that a low-priority external request does not evict the owner's `complex-model` from VRAM, prioritizing already-hot models for non-critical tasks to preserve maximum system throughput.

#### DAGs
A Directed Acyclic Graph (DAG) represents a sequence of sub-tasks where the execution of one task strictly depends on the output of previous tasks, preventing circular logic or infinite loops. In OpenClaw, Team Leads (like the `software_architect`) operate as DAG planners to organize agent swarms.

**Example Prompt:** *"Write a flutter app that provides a dashboard showing the battery status of registered devices, that will run on Android and iOS phones as well as within Chrome browsers."*

**DAG Generation:**
Instead of trying to write the entire app itself, the `software_architect` decomposes the problem and generates a structured dependency graph:
1.  **Task A (Design):** `software_architect` drafts the Flutter widget hierarchy, state management approach (e.g., Riverpod), and battery API interfaces. (Delegated to itself, `complex-model`).
2.  **Task B (Implementation):** `software_dev` receives Task A's output and writes the Dart code for the iOS/Android platform channels and web abstractions. (Depends on A, `medium-model`).
3.  **Task C (Testing):** `qa_engineer` writes unit tests for the state manager and mocks the battery API responses. (Depends on B, `medium-model`).
4.  **Task D (Review):** `project_manager` reviews the final codebase against the user's initial prompt requirements before presenting the final output. (Depends on C, `simple-model`).

**Collaborative vs. Autonomous Coding:**
*   **Collaborative (Human-in-the-Loop):** The DAG pauses at predefined waypoints. The `software_architect` presents the structural design (Task A) to the human user for approval. If approved, the DAG resumes execution, allowing the developer to write the code. Fast Time-To-First-Token (TTFT) is critical here to keep the human engaged.
*   **Autonomous Coding:** The swarm executes the entire DAG independently. The `qa_engineer` might fail the test in Task C, dynamically appending a new "Fix Code" node back to the `software_dev`, completely without human intervention. In this mode, total processing time matters more than TTFT, and deterministic model routing (explicitly assigning specific local models directly to the QA engineer) is vastly more efficient than repeatedly invoking a dynamic prompt-to-model judge.

#### Pre-Execution Routing Hooks (Middleware)
Routing Hooks are lightweight interceptor scripts (such as OpenClaw's native `lexical_predictive.js` workspace plugin) that function as a critical routing tool. They catch prompts in-flight before they ever reach the target model or the proxy layer.

This capability allows operators to inject custom JavaScript or Python logic to dynamically rewrite the targeted model string, enforce hard cost boundaries, or execute the LLM-as-a-Judge API calls outside the core framework source code. By utilizing middleware hooks, the framework maintains extreme flexibility, allowing complex prompt-to-model logic to be executed and tested without requiring modifications to the upstream Gateway binaries.

#### Context Caching (Prompt Caching)
Context caching is an optimization capability that allows the inference engine to store the KV-cache of frequently used system prompts, massive documents, or conversation histories. Instead of recomputing the tokens for the entire context window on every turn, the engine instantly recalls the cached state and only computes the new user message.

This tool heavily mitigates the token cost and latency weaknesses inherent in the Middle Reasoning DAG implementation. If the Orchestrator, Team Lead, and Worker share significant overlapping context (such as the same `AGENTS.md` definitions), context caching ensures that the repeated transmission of this data across the DAG does not burn through API budgets or induce massive Time-To-First-Token delays.
