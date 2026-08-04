# MetaClaw Changelog

## [2026-08-02] - Metrics Observability Stack

### Added

*   Introduced the `tsdb` (Time-Series Database), `collector` (Metrics
    Collector), and `visualizer` (Data Visualizer) service categories.
*   Implemented `victoriametrics` provider for the `tsdb` service.
*   Implemented `telegraf` provider for the `collector` service.
*   Implemented `grafana` provider for the `visualizer` service.
*   Added stubs for various alternative providers across all three new
    services.

### Changed

*   Updated `bin/orchestrate.py` and `bin/cluster_setup.py` to dynamically
    allocate TSDBs to the Archive plane and Visualizers to the Control plane,
    while globally distributing Collectors to all edge nodes.

### Fixed

*   Fixed `grafana` startup crash caused by Docker root volume mount
    permissions by injecting an Alpine `grafana-init` container to run
    `chown -R 472:0` prior to boot.
*   Fixed `victoriametrics` syntax crash by updating the retention flag to
    `30d` instead of `1M`.

## [2026-07-28]

### Added

*   Teardown logic in `install.sh` to destroy conflicting global
    `/usr/local/bin/ollama` installations.
*   Custom Modelfile generation (`metaclaw-llama4-scout`) to strictly enforce
    Llama 4 `<|start_header_id|>` boundaries, successfully suppressing the
    `assistant\n\n` generation leak.

### Changed

*   Restored explicit double quotes around `OLLAMA_TARGET_MODELS` in
    `bin/orchestrate.py` to support safe `source .env` execution while
    maintaining Make loop compatibility.
*   Refactored `install.sh` to safely extract Ollama binaries to isolated
    directories, protecting `lib/metaclaw.py` from catastrophic overwrite.

### Fixed

*   `sre_sysadmin` agent crash by adding `execute_shell_command` to its
    allowed tools list.

## [2026-07-26] - Semantic Predictive Routing & Hierarchical Orchestrators

### Added

*   **Semantic-Predictive Routing Initialization:** Added foundational support
    for a hybrid routing architecture combining fast cosine similarity
    (Intent) with a local LLM Judge (Complexity). Includes a Javascript hook
    stub `semantic_predictive.js` to intercept and score payloads at runtime.
*   **Hierarchical Orchestrators:** Refactored the top-level `orchestrator`
    agent into a dedicated team (`lead`, `chat`, `code`, `image`, `video`).
    The `orchestrator_lead` now acts as the `default: true` ingress point to
    mitigate 60-category LMArena hallucination risks by narrowing the
    classification scope for sub-orchestrators.
*   **Context Caching & Multi-Tenant Priority Documentation:** Added
    architectural guidance for utilizing PagedAttention caching and
    configuring the local LiteLLM proxy to handle priority queues for
    external friends accessing the compute farm.

### Changed

*   **Agent Naming Conventions:** Refactored identity documents and routing
    architectures to strictly enforce the `<team>_<member>` agent ID
    nomenclature (e.g., `software_qa` and `software_dev`).
*   **Automated Utterance Generation:** Refactored `patch_routing.py` to
    auto-parse workspace YAMLs and extract `skill_signature` fields into
    `utterances-agents.yaml`, allowing seamless updates to the semantic
    routing vector space without manual intervention.
*   **Agent Semantic Isolation:** Re-wrote `skill_signature` and
    `negative_keywords` across all agents (Health, Self, Social, Media,
    Software, SRE) to establish strictly orthogonal boundaries, dramatically
    reducing semantic bleed during vector projection.
*   **Software Execution Directives:** Updated `software_orchestrator`,
    `software_dev`, and `software_qa` `SOUL.md` files. Deprecated rigid
    parallel testing directories and Bazel compilation. Enforced standard,
    language-idiomatic OOP structures, Makefiles, and automated linters
    (`pylint`, `black`).

### Fixed

*   **Advanced Python Scripts Resolution:** Modified `test_thresholds.py`,
    `plot_clusters.py`, and `generate_router.py` to securely anchor relative
    paths using `os.path.abspath(__file__)`, preventing crashes when executed
    outside the repository root.
*   **Headless Plotting:** Fixed `plot_clusters.py` crashing on headless Tier
    2 nodes by swapping `plt.show()` for `plt.savefig()`.
*   **Dynamic Auth Key Retrieval:** Repaired `test_thresholds.py` and
    `plot_clusters.py` to dynamically fetch the `ACTIVE_PROXY_KEY` and target
    Tailscale IPs directly from `.env.json` and `profile.json`, rather than
    relying on legacy hardcoded `localhost` variables.
*   **Cluster Setup IP Mapping:** Fixed a bug in `bin/cluster_setup.py` where
    the master node erroneously stored its LAN IP instead of its `100.x.y.z`
    Tailscale IP in `profile.json` due to hostname string mismatches.

## [2026-07-21] - Arena Taxonomies & TTY Stability

### Added

*   **Agent YAML Testing Block:** Added support for a `tests:` array within
    individual agent YAML definitions. `bin/openclaw_test.py` now dynamically
    parses these files to allow per-agent, per-complexity unit testing,
    replacing global hardcoded test prompts.
*   **Playwright Arena Fetcher:** Introduced `bin/fetch_arena.py` to extract
    raw, fully-rendered Gradio JSON state payloads directly from
    `https://arena.ai/leaderboard`. This unlocks the ability to parse
    granular sub-domain/category triplets for dynamic ELO-based
    prompt-to-model routing.

### Changed

*   **Remote SSH TTY Allocation:** Modified `run_remote()` in
    `bin/cluster_setup.py` to inject the `-t` pseudo-terminal flag when
    executing non-hidden commands. This fixes an issue where `make setup`
    would hang indefinitely when attempting to prompt the user for `.env`
    variables over an SSH pipe.

### Fixed

*   **Predictive Judge Schema Crash:** Fixed `lexical_predictive.js` to
    return `null` instead of `{}` when bypassing the Predictive Judge for
    leaf nodes. This resolves HTTP 500 "api_error" crashes triggered by
    strict schema validation in the OpenClaw gateway.
*   **APU Vulkan Variable Scoping:** Fixed a critical deployment bug where
    `bin/orchestrate.py` and `.env.template` blindly prompted and injected
    AMD APU-specific overrides (`OLLAMA_VULKAN=1`,
    `HSA_OVERRIDE_GFX_VERSION=11.0.0`) globally across all nodes. The script
    now correctly scopes these variables strictly to Linux nodes where an AMD
    APU is detected in the hardware profile.
*   **Missing Index Documentation Crash:** Added a bash file-existence check
    to `prep-instructions` in `services/gateways/openclaw/Makefile` to
    prevent `make wizard-cluster` from halting when `index.md` has not yet
    been generated.

## [2026-07-20] - Hardware Enablement & Telemetry Decoupling

### Added

*   **Forwarders Service Taxonomy:** Introduced the `forwarders` service
    category. Fluidly decoupled log collection agents (Fluent Bit, Vector)
    from Log Storage engines (VictoriaLogs, ELK).
*   **Global Telemetry Mesh:** Orchestrator now forces `forwarders` onto
    every node in the cluster, injecting `HOST_IDENTIFIER` to tag logs by
    Tailscale IP.
*   **Docker Origin Enrichment:** Fluent Bit now mounts the Docker socket,
    dynamically resolving container IDs to human-readable names
    (`_container_name`) in the VictoriaLogs index.

### Changed

*   **Timeout Extensions:** Elevated proxy and test script timeouts from 300s
    to 600s/900s to support lengthy VRAM weight-loading delays for 100B+
    parameter models.

### Fixed

*   **APU Hardware Acceleration (Strix Halo):** Upgraded target Linux kernels
    to 7.0 via the official Ubuntu HWE stack to introduce missing RDNA 3.5
    drivers.
*   **Ollama APU Vulkan Initialization:** Injected `OLLAMA_VULKAN=1` and
    `OLLAMA_IGPU_ENABLE=1` overrides, and forced `ROCR_VISIBLE_DEVICES="none"`
    to bypass AMD ROCm's Shared Virtual Memory (SVM) hard-limits. This allows
    the Vulkan driver to detect and fully utilize the BIOS-allocated 96GB UMA
    Frame Buffer on Strix Halo APUs, preventing catastrophic swap thrashing
    during heavy context loads. Eliminated conflicting `HIP_VISIBLE_DEVICES`
    blinders that forced CPU fallbacks.

## [2026-06-08] - Cluster Provisioning & Network Resilience

### Added

*   **Native SSH Orchestration:** Replaced `fabric/paramiko` with
    `subprocess` calling native `ssh` and `scp`. This securely negotiates
    Tailscale's "none" authentication mechanism.
*   **Global Secrets Sync (Phase 4):** `cluster_setup.py` now leverages `jq`
    over SSH to securely merge `ACTIVE_PROXY_KEY` and `GEMINI_API_KEY` into
    remote `.env.json` files without destroying node-specific state.
*   **Centralized Cluster Status:** Added `bin/cluster_status.py` and the
    `make status` root target to iteratively poll both Docker and bare-metal
    services across the unified `profile.json` topology.
*   **Dynamic RAM Modeling:** `orchestrate.py` now evaluates remote node
    `ram_gb` limits, gracefully assigning `qwen-3-32b` to nodes < 90GB RAM,
    and `llama4-scout-q4:109b` to high-capacity nodes.

### Fixed

*   **Tailscale Lifeline Protection:** Implemented strict `.metal` and
    `headless` detection. The framework will no longer attempt to deploy
    Dockerized Tailscale on nodes that already rely on bare-metal Tailscale
    for remote SSH access.
*   **Ollama Daemon SIGHUP:** Modified `services/runners/ollama/Makefile` to
    launch the daemon with `nohup` and redirected `stdin`, preventing the
    daemon from instantly terminating when the remote SSH bootstrap session
    disconnects.
*   **OpenClaw Gateway Patching:** Fixed `patch_routing.py` to inject
    600-second timeouts for massive local LLM cold-starts, properly inject
    the Proxy API key for the `prompt-embedding-model`, and enable both
    `sessions.visibility="all"` and `tools.agentToAgent.enabled=true` to
    satisfy legacy schema validation.
