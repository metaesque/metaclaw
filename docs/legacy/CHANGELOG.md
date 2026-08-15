# MetaClaw Changelog

## [2026-08-07] - ClawDisk Decentralized Storage Mesh Stabilization

### Added

*   **Modular Feature Subsystem:** Extracted ClawDisk logic from `lib/devices.py` into a standalone modular feature script (`features/clawdisk/bin/clawdisk_setup.py`) to prevent God-Object bloat in the core library API.
*   **GitOps Pull Config Target:** Implemented `bin/fetch_hardware_state.py` and the `make pullcfg` target in the global `Makefile`. This provides a secure, targeted `rsync` mechanism to marshal dynamically generated hardware states (like discovered SSD mount points) from edge nodes back to the `../config/data/hardware/node/` drop-zone on the operator's laptop without tromping on other hosts' data.

### Changed

*   **Stateless AutoFS Failover:** Replaced brittle `current_host` symlinking logic with native AutoFS replicated server failover. The daemon now receives a comma-separated list of all dynamic cluster IPs (parsed directly from `profile.json` instead of static hardware files) and natively attempts to mount the SSD from whichever physical node responds.
*   **Automated Node Setup Trigger:** Modified `make apply` in the root `Makefile` to automatically execute `bin/node_setup.py` during reconciliation, ensuring new storage meshes and host modifications are applied alongside Docker container updates.

### Fixed

*   **exFAT NFS Kernel Bypass:** Discovered that the modern Linux in-kernel `exfat` driver fundamentally rejects NFS `export_operations`. Implemented a dynamic FUSE bypass that forces `exfat` drives to mount via the older userspace `exfat-fuse` driver, allowing them to successfully export over the LAN.
*   **AutoFS Local Hijack Deadlock:** Fixed a bug where AutoFS would mistakenly generate network mount triggers for drives physically attached to the local machine, causing self-referential `No such file or directory` deadlocks during `cd`.
*   **AutoFS Syntax Compliance:** Fixed malformed space-separated replicated server syntax (`ip1:/path ip2:/path`), converting it to the strictly required comma-separated format (`ip1,ip2:/path`) and removing deprecated `intr` flags.

## [2026-08-06] - Storage, Jinja2 Templating, and Container Escapes

### Added

*   **Context Optimization:** Created `docs/MANIFEST-core.files` and
    `docs/MANIFEST-extra.files` to efficiently split framework boundaries for
    LLM context ingestion.
*   **Configuration Payloads:** Added `docs/CONFIG.files` and a new `make cfg`
    target to the root `Makefile` to compile JSON data into LLM payloads.
*   **Jinja2 Templating:** Introduced `docs/personal/Wade.md.j2` and
    `bin/render_templates.py` to programmatically render markdown
    documentation directly from the `hardware.json` registry.
*   **Hardware Registry Mounts:** Added external Samsung T7/T9 SSDs and
    network/power assets to `config/data/hardware.json`. Introduced a `mounts`
    array schema to explicitly map filesystem UUIDs and block sizes.
*   **Hardware-Agnostic Polling:** Implemented `poll_amd_sysfs()` to read GPU
    telemetry natively from `/sys/class/drm/card*`, bypassing the need for
    external drivers on AMD nodes. Created `poll_nvidia()` for GB10 Spark
    nodes.
*   **Dashboard Integration:** Updated Grafana's `dashboard.json` to plot
    `gpu_telemetry_utilization` and `gpu_telemetry_vram_used_mb`, dynamically
    mapping PromQL variables to cluster hosts.

### Changed

*   **Workspace Optimization:** Updated the `make wksp` target to explicitly
    exclude `-huge.json` files to prevent context bloat.
*   **Container Escape via Chroot:** Updated the `gpu_telemetry.py` script to
    utilize a `chroot /hostfs` wrapper. This allows the Telegraf Docker
    container to execute the host OS's native binaries (like `nvidia-smi`) and
    dynamically link host driver libraries.
*   **CGroup Bypassing:** Elevated the Telegraf container to `privileged: true`
    to bypass strict Linux CGroup policies, granting it full hardware
    visibility and access to `/dev/nvidiactl` character devices.
*   **The Telegraf Entrypoint Paradox:** Overrode the default Docker
    `entrypoint.sh` for Telegraf (which forcibly dropped root privileges to UID
    999) by setting `entrypoint: ["telegraf"]` and `user: root`. This restores
    the permissions necessary to run the chroot syscall for the background
    daemon.

### Fixed

*   **YAML Syntax Escaping:** Fixed a container boot failure in the Grafana
    visualizer by correctly escaping backslashes (`\\s*`) within double-quoted
    YAML scalars in the healthcheck regex.

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
