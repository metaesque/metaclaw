# MetaClaw Changelog

## [2026.7.20] - Hardware Enablement & Telemetry Decoupling

### Added
*   **Forwarders Service Taxonomy:** Introduced the `forwarders` service category. Fluidly decoupled log collection agents (Fluent Bit, Vector) from Log Storage engines (VictoriaLogs, ELK).
*   **Global Telemetry Mesh:** Orchestrator now forces `forwarders` onto every node in the cluster, injecting `HOST_IDENTIFIER` to tag logs by Tailscale IP.
*   **Docker Origin Enrichment:** Fluent Bit now mounts the Docker socket, dynamically resolving container IDs to human-readable names (`_container_name`) in the VictoriaLogs index.

### Changed
*   **Timeout Extensions:** Elevated proxy and test script timeouts from 300s to 600s/900s to support lengthy VRAM weight-loading delays for 100B+ parameter models.

### Fixed
*   **APU Hardware Acceleration (Strix Halo):** Upgraded target Linux kernels to 7.0 via the official Ubuntu HWE stack to introduce missing RDNA 3.5 drivers.
*   **Ollama APU Vulkan Initialization:** Injected `OLLAMA_VULKAN=1` and `OLLAMA_IGPU_ENABLE=1` overrides, and forced `ROCR_VISIBLE_DEVICES="none"` to bypass AMD ROCm's Shared Virtual Memory (SVM) hard-limits. This allows the Vulkan driver to detect and fully utilize the BIOS-allocated 96GB UMA Frame Buffer on Strix Halo APUs, preventing catastrophic swap thrashing during heavy context loads. Eliminated conflicting `HIP_VISIBLE_DEVICES` blinders that forced CPU fallbacks.

## [2026.6.8] - Cluster Provisioning & Network Resilience

### Added
*   **Native SSH Orchestration:** Replaced `fabric/paramiko` with `subprocess` calling native `ssh` and `scp`. This securely negotiates Tailscale's "none" authentication mechanism.
*   **Global Secrets Sync (Phase 4):** `cluster_setup.py` now leverages `jq` over SSH to securely merge `ACTIVE_PROXY_KEY` and `GEMINI_API_KEY` into remote `.env.json` files without destroying node-specific state.
*   **Centralized Cluster Status:** Added `bin/cluster_status.py` and the `make status` root target to iteratively poll both Docker and bare-metal services across the unified `profile.json` topology.
*   **Dynamic RAM Modeling:** `orchestrate.py` now evaluates remote node `ram_gb` limits, gracefully assigning `qwen-3-32b` to nodes < 90GB RAM, and `llama4-scout-q4:109b` to high-capacity nodes.

### Fixed
*   **Tailscale Lifeline Protection:** Implemented strict `.metal` and `headless` detection. The framework will no longer attempt to deploy Dockerized Tailscale on nodes that already rely on bare-metal Tailscale for remote SSH access.
*   **Ollama Daemon SIGHUP:** Modified `services/runners/ollama/Makefile` to launch the daemon with `nohup` and redirected `stdin`, preventing the daemon from instantly terminating when the remote SSH bootstrap session disconnects.
*   **OpenClaw Gateway Patching:** Fixed `patch_routing.py` to inject 600-second timeouts for massive local LLM cold-starts, properly inject the Proxy API key for the `prompt-embedding-model`, and enable both `sessions.visibility="all"` and `tools.agentToAgent.enabled=true` to satisfy legacy schema validation.
