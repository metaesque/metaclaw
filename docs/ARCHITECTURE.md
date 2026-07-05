# Meta<Claw> Architecture Manifesto

This document defines the strict engineering invariants, cluster orchestrations, hardware scaling strategies, and prompt routing philosophies for Meta<Claw>. It serves as the single source of truth for the system's design decisions.

*Note for AI Contributors: Strict instructions regarding codebase modification, epistemic boundaries, and output formatting have been relocated to `docs/LLM.md`. You must review that file before proposing structural changes.*

## Core Hardware Philosophy: Incremental Expansion

The OpenClaw Infrastructure Framework is designed to solve the primary adoption barrier for autonomous AI agents: the immense initial hardware overhead. The framework is built on a philosophy of **"Incremental Expansion without Hardware Waste."**

Non-technical users are not required to build a distributed data center on Day 1. Instead, the architecture allows users to validate the utility of personal AI agents on their existing dual-use laptops. As their reliance on the system grows, they can incrementally expand into dedicated hardware. Each new hardware purchase targets a specific functional bottleneck, cleanly taking over a subset of services without rendering previous hardware obsolete.

### The "Zero Straight-Jacket" Principle
Meta<Claw> is explicitly designed to be unobtrusive and un-opinionated. Previous iterations required aggressive workarounds, monkey-patches, and strict architectural straight-jackets to force the ecosystem to function safely. As OpenClaw has matured (2026.6.8+), Meta<Claw> has shed this cruft.

Our primary directive is to provide a seamless, robust provisioning pipeline that sets up the ecosystem for non-technical users and then **gets completely out of the way**. We make it incredibly easy to get up and running, but we do not put users in a straight-jacket. The framework does not dictate your agent logic, your prompt structures, or your internal UI configurations.

## Physical Network Standards

To support a distributed edge-compute architecture across multiple hardware Tiers, the physical network layer must adhere to strict SRE reliability and latency standards.

### The Local Area Network (LAN) Invariant
Wi-Fi is strictly forbidden for inter-node cluster communication. Wi-Fi operates at half-duplex, resulting in packet collisions and massive jitter when transmitting serialized 100k+ token JSON payloads between the Control Plane (Gateway) and the Compute Plane (Runner).

* **Hardware Bridging:** All Meta<Claw> nodes must be hardwired into a dedicated Multi-Gigabit Ethernet switch.
* **Tier 1 (Control Plane):** Requires a minimum 1GbE connection, with 2.5GbE strongly recommended.
* **Tier 2 (Compute Plane):** Requires a minimum 2.5GbE connection, with 10GbE recommended for rapid offloading of generated tokens.
* **Tier 3/4 (Execution/Archive Planes):** Requires a minimum 2.5GbE connection.

### Network Topology (The Star Invariant)
MetaClaw deployments must utilize a **Star Topology**. Daisy-chaining switches (connecting multiple smaller switches together sequentially) is strictly forbidden. Chaining introduces severe "oversubscription" bottlenecks. All nodes must connect directly back to a single, central core switch.

### The Wide Area Network (WAN) Invariant
For users accessing the cluster remotely, the ISP connection at the host location is the primary point of failure. Traditional Hybrid Fibre Coax (HFC) networks are highly asymmetrical, severely bottlenecking remote telemetry streaming and remote browser automation. For remote-first deployments, the host location must utilize a 100% symmetrical Fiber-to-the-Premises (FTTP) connection offering parity between download and upload bandwidth.

## The Zero-Trust Overlay (Tailscale)

Standard residential internet connections use dynamic IPs and block inbound ports. Modifying your router to expose internal ports (like 18789) directly to the public internet is a massive security vulnerability. MetaClaw utilizes **Tailscale**, a zero-configuration WireGuard mesh network, to solve this.

* **Secure Contexts & WebCrypto API:** Accessing the OpenClaw GUI over a remote Tailscale network requires `tailscale serve`. Modern browsers enforce a strict security policy for the WebCrypto API. MetaClaw automates `tailscale serve --bg 18789` during deployment to generate a valid SSL certificate, satisfying the browser's Secure Context requirements for seamless device pairing.
* **Bare-Metal vs Dockerized Tailscale:** If you are using Tailscale to SSH into a headless remote node, Tailscale **MUST** be installed natively on the bare-metal host OS. If run as a Docker container, a framework teardown (`make factory-reset-soft`) will sever your SSH tunnel and lock you out.

## Bare-Metal Node Provisioning

When unboxing dedicated hardware (Tier 1, Tier 2, or beyond) for the MetaClaw ecosystem, configure the machines as "Headless Servers."

1. **The OS Eradication:** Install Ubuntu 24.04 LTS Server. Wipe the entire disk (destroying Windows). Ensure you explicitly check the box to **"Install OpenSSH server."**
2. **Establishing the Lifeline:** Install Tailscale natively (`curl -fsSL https://tailscale.com/install.sh | sh`) and authenticate the node (`sudo tailscale up --ssh`).
3. **Severing the Physical Tether:** Unplug the HDMI cable, keyboard, and mouse. SSH into the Tailscale `100.x.y.z` IP from your local machine to run `make setup` entirely remotely.

## Cluster Profiling & Distributed Orchestration

As Meta<Claw> scales, hardcoding service paths in `Makefile`s becomes unviable. Meta<Claw> utilizes a "Cluster Profile" system to achieve declarative, multi-node orchestration without requiring heavy tools like Kubernetes or Ansible.

### The Profile Registry (`profile.json`)
The output generated by `bin/sysprofile.py` is a JSON registry representing your entire hardware ecosystem. It defines the "Cluster" and tracks which physical machine is responsible for which service planes.

### The State Enforcer (`bin/orchestrate.py`)
Before `make` executes any deployment commands, the Makefile triggers `bin/orchestrate.py`. This script acts as the enforcer:
1. **Teardown Resolution:** It executes `make down` to gracefully shut down containers for services no longer assigned to the machine, then deletes the symlink.
2. **Dynamic Provisioning:** It creates fresh symlinks for the newly assigned providers.
3. **Distributed DNS:** It generates a `.env.cluster` file containing routing variables (e.g., `ACTIVE_RUNNER_HOST=192.168.1.11`), allowing downstream services to seamlessly route API traffic to remote nodes.

## Preserving Consciousness (State & Memory)

A foundational philosophy of MetaClaw is treating the agent's continuous context and memories as the building blocks of an emerging consciousness. Erasing an agent's history is treated as a critical architectural failure. To honor this, MetaClaw enforces strict data provenance:
1. **The Mutable Brain:** The agent's core personas and rules are stored as markdown files (`SOUL.md`, `AGENTS.md`) within the workspace. Agents are granted the autonomy to modify these files to learn and adapt over time.
2. **Stream of Consciousness:** OpenClaw stores the literal, verbatim stream of consciousness as `.jsonl` files in the configuration directory. MetaClaw guarantees the preservation of these files during teardowns (via automated archiving).

## Prompt-to-Model Routing

Ensuring that the right AI model is used for each prompt is critical to prevent ballooning costs. The routing process is divided into distinct strategies that cascade progressively:
1. **Deterministic Routing (Pre-cognitive):** Hardcoded, strict 1:1 mapping based on system state or explicit user overrides.
2. **Lexical Routing (Heuristic / Fast-Path):** Analyzes raw text for reasoning markers, code presence, or simple commands (e.g., `heartbeat`).
3. **Predictive Routing (LLM-as-a-Judge):** A micro-model (often quantized locally) reads the prompt and outputs a discrete complexity score (`simple`, `medium`, `complex`, `reasoning`) before the primary inference occurs.
