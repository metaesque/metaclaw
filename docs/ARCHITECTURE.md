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
   [https://tailscale.com/install.sh](https://tailscale.com/install.sh) | sh`) and authenticate the node (`sudo
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
2. **The Vulkan Workaround:** Ollama's bundled ROCm/HIP binaries strictly check PCI IDs. They frequently reject novel architectures like RDNA 3.5 (`gfx1151`). To force acceleration, MetaClaw injects `OLLAMA_VULKAN=1` and `OLLAMA_IGPU_ENABLE=1` to utilize the universal Vulkan compute engine.
3. **The Blanking Mandate:** You must **never** inject `HIP_VISIBLE_DEVICES=-1` to bypass ROCm. Doing so blinds the hardware enumeration scanner entirely, causing Ollama to instantly abort the Vulkan initialization and fall back to CPU.

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

3. **Conceptual Models:** Agents must request models using conceptual
   abstraction (e.g., `simple-model`, `medium-model`, `complex-model`,
   `frontier-model`) or explicit specialty models (e.g., `flux-1-dev`). They
   must NOT hardcode hardware-specific parameters (e.g., `qwen-3-32b`). The
   LiteLLM proxy handles the physical mapping based on the active hardware Tier.

Because building resilient multi-agent swarms requires hard-won architectural
lessons, the MetaClaw repository includes a `.workspace.template` directory
acting as an educational "example" workspace. During initial provisioning, the
`bin/customize.py` script can optionally copy this template into the sibling
`../workspace` directory to give non-technical users a functional baseline.
Advanced users are encouraged to maintain their own private, heavily customized
workspace repositories and ignore the template entirely.

## Prompt-to-Model Routing & "Middle Reasoning"

Ensuring that the right AI model is used for each prompt is critical to prevent
ballooning costs (Context Drag). MetaClaw enforces a **Hierarchical Task Network
(HTN)** topology known as "Middle Reasoning."

1. **The Orchestrator:** Uses a `medium-model` to act as a switchboard, mapping
   user intents to specific Team Leads.

2. **Team Leads (Middle Reasoning):** Use `complex-model` or `frontier-model`.
   They receive intents, synthesize constraints, and output a Directed Acyclic
   Graph (DAG) of sub-tasks. Team Leads are strictly stripped of execution tools
   (like `read_file` or `search_web`); they MUST delegate downwards using
   `sessions_send`.

3. **Leaf Nodes (Execution):** Workers (like `software_dev`) use
   `medium-model` or `simple-model` to execute discrete tools.

### The 4-Tier Judge

The `lexical_predictive.js` hook intercepts prompts sent to Team Leads and asks
a local judge (e.g., `gemma4:e4b`) to score complexity mechanically:

1. `simple`: Factual queries, basic translation, trivial tools.
2. `medium`: Summarization, standard business logic.
3. `complex`: System architecture, advanced coding, data pipelines.
4. `frontier`: Extreme context, zero-shot DAG generation.

*Crucially*, if the target agent is a Leaf Node (lacking the `is_lead: true`
flag in its YAML), the JS hook bypasses the Judge entirely, allowing the agent
to use its designated specialty model without interference.
