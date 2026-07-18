# MetaClaw Architecture Roadmap

This document outlines the strategic evolution of the MetaClaw framework, tracking technical debt, planned features, and architectural pivots identified during deployment testing.

## Phase 1: Foundation (Current)
*   [x] Establish the `openclaw-network` mesh.
*   [x] Implement `profile.json` dynamic orchestration.
*   [x] Establish Tier 0 (Minilith) and Tier 2 (Compute Farm) baseline topologies.
*   [x] Implement LiteLLM fallback chains (`medium-model` -> `gemini-2.5-flash`).
*   [x] Distribute workloads via Tailscale SSH integration.

## Phase 2: Distributed State & Observability (Upcoming)
*   **[TODO] Distributed Logging (VictoriaLogs & Fluent Bit):**
    Currently, VictoriaLogs only aggregates Docker JSON logs from the local `control` node. We need to explicitly configure `fluent-bit.conf` to tail bare-metal log files (e.g., `services/runners/ollama/ollama.log`) and deploy lightweight Fluent Bit forwarders to all remote `compute` and `execution` nodes to push telemetry back to the centralized `ACTIVE_LOGGER_HOST`.
*   **[TODO] Dynamic Model Sizing Refinement:**
    The orchestrator currently implements a basic RAM gate for `llama4-scout` vs `qwen-3`. This must be refactored to dynamically calculate precise VRAM offload capabilities across arbitrary GPU arrays (NVIDIA vs AMD), gracefully falling back through a wider gradient of quantized models (e.g., 70B, 32B, or 8B).
*   **[TODO] Pre-Warming Models via `wizard-cluster`:**
    Ollama performs cold-start tensor allocations upon the first API request, causing initial delays on massive models. Implement a background `curl` request inside `bin/wizard_cluster.py` to trigger the allocation sequence during the setup phase, ensuring models are "hot" before the user begins agent interactions.

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
