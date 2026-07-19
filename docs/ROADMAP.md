# MetaClaw Architecture Roadmap

This document outlines the strategic evolution of the MetaClaw framework, tracking technical debt, planned features, and architectural pivots identified during deployment testing.

## Phase 1: Foundation (Current)
*   [x] Establish the `openclaw-network` mesh.
*   [x] Implement `profile.json` dynamic orchestration.
*   [x] Establish Tier 0 (Minilith) and Tier 2 (Compute Farm) baseline topologies.
*   [x] Implement LiteLLM fallback chains (`medium-model` -> `gemini-2.5-flash`).
*   [x] Distribute workloads via Tailscale SSH integration using native `subprocess`.

## Hardware Optimization (Pending Actions)
*   **[TODO] Reclaim UMA Frame Buffer RAM (Control Node):**
    The GMKtec K8 Plus currently reserves ~3.78GB of RAM for the integrated Radeon 780M graphics (UMA Frame Buffer). Because the node runs headless (no display), this memory is wasted and hidden from the OS.
    **Action Required:** Reboot the K8 Plus, enter the BIOS (`Del` or `F2`), navigate to **Advanced -> AMD CBS -> NBIO Common Options -> GFX Configuration -> UMA Frame buffer Size**, and change it to `Auto` or `512MB`. This will free up RAM for Docker services, while the GPU continues to dynamically allocate inference memory via GTT.
*   **[URGENT] Kernel Upgrade for Strix Halo (Compute Node):**
    The GMKtec EVO-X2 features bleeding-edge RDNA 3.5 graphics. The default Ubuntu Linux 6.8 kernel does not possess the drivers to detect the GPU, forcing Ollama into extreme CPU-only bottlenecks (70s+ response times).
    **Action Required:** Upgrade the Linux Kernel on the Compute node to 6.11+ and install the latest `amdgpu-dkms` drivers to unlock hardware acceleration.

## Phase 2: Distributed State & Observability (Upcoming)
*   **[TODO] Service Taxonomy Refactor:**
    Currently, storage databases (VictoriaLogs, ELK) and edge agents (Fluent Bit, Vector) are incorrectly grouped in `services/loggers`. We must introduce a new `services/forwarders` (or `telemetry-agents`) category to properly decouple storage from collection.
*   **[TODO] Distributed Logging (VictoriaLogs & Fluent Bit):**
    Once the taxonomy is fixed, deploy lightweight Fluent Bit forwarders to all remote `compute` and `execution` nodes to tail bare-metal logs (like `ollama.log`) and push telemetry back to the centralized `ACTIVE_LOGGER_HOST`.
*   **[TODO] Dynamic `num_ctx` Calculation:**
    While models like `llama4-scout` have massive context limits, Ollama defaults API requests to 2048 tokens. Instead of hardcoding fixes in LiteLLM, refactor `bin/cluster_setup.py` to dynamically calculate safe `num_ctx` ceilings based on the model's footprint and the host's detected VRAM, propagating the limits to `.env.cluster`.

## Phase 3: The Execution Plane (Sandboxing)
*   **[TODO] Docker-out-of-Docker (DooD) Integration:**
    Implement the secure workspace jails (`services/sandboxes/docker-dood`) to allow agents to write, execute, and iteratively debug code in isolated environments.
*   **[TODO] Browser Automation Automation:**
    Integrate `browseruse` and `stagehand` to allow the research agents to autonomously navigate dynamic SPAs and scrape live documentation.

## Phase 4: Data Sovereignty
*   **[TODO] PostgreSQL High Availability:**
    Transition the single-node pgvector instance to a clustered topology for Tier 4 deployments to ensure conversation history survives physical node failures.
*   **[TODO] Local Embedding Replacement:**
    Currently, the OpenClaw `prompt-embedding-model` relies on Google Gemini. Transition this to a local, high-speed embedding model (e.g., `nomic-embed-text`) running natively on the `control` node to achieve 100% air-gapped privacy.

## Phase 5: Testing Infrastructure (Upcoming)
*   **[TODO] Architectural Testing & Benchmarking:**
    Establish a standardized testing infrastructure to evaluate the optimal execution locations for various models. The framework must support configurable matrix testing (e.g., testing Model A on Host X versus Model B on Host Y) to empirically prove latency hypotheses (such as whether `judge-model` performs faster on the control node versus the compute node).
