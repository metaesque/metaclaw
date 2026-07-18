# MetaClaw Changelog

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
