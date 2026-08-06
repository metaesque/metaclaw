# MetaClaw Architecture Roadmap

This document outlines the strategic evolution of the MetaClaw framework, tracking technical debt, planned features, and architectural pivots identified during deployment testing.

## Immediate Action Items (Transferred from Previous Session)
*   **[x] Grafana Dashboard Static Provisioning:**
    Restructured the `workspace/src/projects/kasa/grafana` directory to map
    correctly to `/etc/grafana/provisioning` schemas. The mount itself is
    handled via `apply_infrastructure_patches.sh`.
*   **[x] Finalize GPU Telemetry Isolation:**
    Telegraf has been patched to use a Debian base image. The `gpu_telemetry.py`
    script has been rewritten to natively read `/sys/class/drm/` metrics from
    the kernel, completely eliminating the need for `cron` or brittle CLI binaries.

## Phase 1: Foundation (Current)
*   [x] Establish the `openclaw-network` mesh.
*   [x] Implement `profile.json` dynamic orchestration.
*   [x] Establish Tier 0 (Minilith) and Tier 2 (Compute Farm) baseline
        topologies.
*   [x] Implement LiteLLM fallback chains (`medium-model` -> `gemini-2.5-flash`).
*   [x] Distribute workloads via Tailscale SSH integration using native
        `subprocess`.
*   [x] Introduce the `tsdb` (Time-Series Database), `collector`
        (Metrics Collector), and `visualizer` (Data Visualizer) services.

## Hardware Optimization (Pending Actions)
*   **[TODO] Reclaim UMA Frame Buffer RAM:**
    The GMKtec K8 Plus currently reserves ~3.78GB of RAM for the integrated
    Radeon 780M graphics (UMA Frame Buffer). Because the node runs headless (no
    display), this memory is wasted and hidden from the OS.
    **Action Required:** Reboot the K8 Plus, enter the BIOS (`Del` or `F2`),
    navigate to **Advanced -> AMD CBS -> NBIO Common Options -> GFX
    Configuration -> UMA Frame buffer Size**, and change it to `Auto` or
    `512MB`. This will free up RAM for Docker services, while the GPU continues
    to dynamically allocate inference memory via GTT.

## Phase 2: Distributed State & Observability (Upcoming)
*   **[x] Kasa Migration (From Project to Core SRE):**
    Acknowledge that Kasa is not a standard workspace project, but a core
    SRE capability that monitors host infrastructure. It has been successfully
    migrated out of the `workspace/` repository and embedded natively into
    MetaClaw's `features/kasa/` module.
*   **[TODO] Implement VictoriaMetrics Timeseries Rewriter:**
    Develop a general-purpose Python script utilizing the VictoriaMetrics `/api/v1/export` and `/api/v1/admin/tsdb/delete_series` endpoints to correct bad data (e.g., retroactively fixing mistaken device alias allocations).
*   **[TODO] Monitor Host Storage and Log Sizes:**
    Add support to the monitoring feature to track the physical size of log files (VictoriaLogs) and general disk usage footprint incurred by MetaClaw on the host machines, to ensure SSDs do not reach capacity unnoticed.
*   **[TODO] All-in-One Platform Providers:**
    Address multi-service providers (such as SigNoz or OpenObserve) that span
    multiple service categories (`logger`, `tracer`, `visualizer`). Currently,
    MetaClaw treats every service as strictly orthogonal, which risks spinning
    up duplicate container stacks if the same provider is selected across
    multiple service roles.
*   **[TODO] Cross-Service Provider Entanglements & Dependencies:**
    Implement declarative inter-provider coupling within `lib/metaclaw.py`. For
    example, selecting `victoriametrics` for the `tsdb` service should
    automatically bias default provider choices for `collector` (`telegraf`) and
    `visualizer` (`grafana`) to ensure maximum compatibility out-of-the-box.
*   **[TODO] Distributed Logging (VictoriaLogs & Fluent Bit):**
    Currently, VictoriaLogs only aggregates Docker JSON logs from the local
    `control` node. We need to explicitly configure `fluent-bit.conf` to tail
    bare-metal log files (e.g., `services/runners/ollama/ollama.log`) and deploy
    lightweight Fluent Bit forwarders to all remote `compute` and `execution`
    nodes to push telemetry back to the centralized `ACTIVE_LOGGER_HOST`.
*   **[TODO] Overcoming `num_ctx` Defaults:**
    While models like `llama4-scout` have massive context limits, Ollama
    defaults API requests to 2048 tokens. OpenClaw Orchestrator prompts
    routinely exceed 7500 tokens. We must implement a centralized mechanism (via
    LiteLLM config or OpenClaw routing patches) to explicitly inject a high
    `num_ctx` (e.g., 16384) to prevent context truncation and subsequent cloud
    fallback.

## Phase 3: The Execution Plane (Sandboxing)
*   **[TODO] Docker-out-of-Docker (DooD Integration):**
    Implement the secure workspace jails (`services/sandboxes/docker-dood`) to
    allow agents to write, execute, and iteratively debug code in isolated
    environments.
*   **[TODO] Browser Automation Automation:**
    Integrate `browseruse` and `stagehand` to allow the research agents to
    autonomously navigate dynamic SPAs and scrape live documentation.

## Phase 4: Data Sovereignty
*   **[TODO] Automate Cross-Cluster Disk Mounting (NFS/Autofs):**
    To ensure true data fluidity across the compute farm, we must dynamically map the `mounts` array within `hardware.json` to automatically generate server-side NFS `/etc/exports` and client-side `/etc/auto.nfs` maps. This abstracts the physical location of the SSDs, allowing seamless access to models, workspaces, and quantified-self archives across all nodes via the Tailscale subnet without saturating bandwidth during idle times.
*   **[TODO] PostgreSQL High Availability:**
    Transition the single-node pgvector instance to a clustered topology for
    Tier 4 deployments to ensure conversation history survives physical node
    failures.
*   **[TODO] Local Embedding Replacement:**
    Currently, the OpenClaw `prompt-embedding-model` relies on Google Gemini.
    Transition this to a local, high-speed embedding model (e.g.,
    `nomic-embed-text`) running natively on the `control` node to achieve 100%
    air-gapped privacy.
*   **[TODO] Multi-Tenant Priority Proxying (LiteLLM):**
    Implement Virtual Key management and rate limiting within the local LiteLLM
    proxy to allow external users (friends) to access the Compute Plane. Ensure
    the proxy maintains a priority queue that privileges internal owner prompts
    to prevent VRAM eviction of hot models during heavy external load.

## Phase 5: Templating Engine Migration (Jinja2)
*   **[~] Transition .env Overrides to Jinja2 Compilation:**
    The current `.env.template` injection system requires complex, rigid Python logic (`orchestrate.py`) to map specific variables. We have begun addressing this by implementing a `bin/render_templates.py` engine that utilizes Jinja2 `.j2` template files for documentation (`Wade.md.j2`). We must now extend this pattern to allow declarative rendering of Compose and Config files directly from `profile.json` node parameters (e.g., `{% if hardware.gpu_detected == "AMD APU" %}`), removing the need for error-prone `change_me_to_` prompt bypasses and global overrides.

## Phase 6: Arena-Driven Model Routing
*   **[TODO] Expand beyond 'Middle Reasoning' DAG:**
    Although we want to maintain support for the 'Middle Reasoning' DAG approach
    to agent orchestration (in which specific models like`complex-model` and `medium-model`
    are explicitly specified in agent YAML definitions), we also want to explore
    other implementations. Need to generalize the agent definitions so that
    different implementations can be selected.
*   **[TODO] Implement LMArena.ai Taxonomy Mapping:**
    Utilize the `bin/fetch_arena.py` script to scrape the live Gradio JSON state
    from LMArena. Modify agent YAMLs to include an `arena_category` parameter
    (e.g., `Chat/Text/Legal & Government`). The Orchestrator will act as a
    single-shot Intent Classifier, passing the prompt to the appropriate agent,
    while MetaClaw's orchestration engine dynamically binds the #1 ranked ELO
    model for that category to the agent executing the task.
*   **[TODO] Implement Runtime Semantic-Predictive Hook:**
    Finish writing the javascript interceptor in
    `services/gateways/openclaw/modules/routing/semantic_predictive.js` to
    natively evaluate cosine similarity at runtime against the `router.json`
    embeddings and forcefully overwrite the `agentId` variable, fully activating
    the semantic routing architecture.

## Phase 7: Unimplemented Services
*   **[TODO] Select and Implement Providers for Unimplemented Services:**
    The following services currently lack functional provider implementations
    (containing only metadata `.provider.json` stubs). We need to select and
    fully implement default providers for each (indicating in [brackets] below
    with working Docker Compose and Makefile infrastructure:
    *   `vcs` (Version Control System) [Gitea]
    *   `ci` (Continuous Integration) [Woodpecker]
    *   `iam` (Identity & Access Management) [Authelia]
    *   `secret` (Secrets Manager) [Doppler]
    *   `tracer` (Distributed Tracer) [Phoenix]
    *   `queue` (Message Queue) [RabbitMQ]
    *   `event` (Event Gateway) [Hookdeck]
    *   `ingress` (Reverse Proxy) [Traefix]

## Phase 8: Technical Debt & Standardization
*   **[x] Standardize Docker Container Naming:**
    Updated all `docker-compose.yml` files, Makefiles, and documentation references across the repository to enforce the `<provider>-<service>` naming convention (e.g., `telegraf-collector`, `postgres-memory`, `fluentbit-forwarder`).
*   **[TODO] Rename the Kasa Feature:**
    Rename the current `features/kasa/` module to `features/metamon/` (MetaMon) to more accurately reflect its role as the comprehensive MetaClaw telemetry and monitoring engine, rather than just a power strip polling script.
*   **[TODO] Python Library Resolution Refactor:**
    Clean up hacky Python library resolution across the codebase. Replace brittle `sys.path.insert` relative path injections and hardcoded data directories with a robust virtual environment path resolution strategy (e.g., `.pth` files or `pip install -e .` editable installs during environment bootstrap).
*   **[TODO] Python Package Namespacing:**
    Move existing library files from `lib/*.py` to `lib/metaclaw/*.py` and introduce `__init__.py` modules. This will allow clean, namespace-bound imports (e.g., `import metaclaw.devices` or `import metaclaw.core`) consistently across all cluster nodes and custom scripts.

## Phase 9: Separation of State & Infrastructure Configuration
*   **[TODO] Implement METACLAW_CONFIG Drop-Zones:** Fully decouple "Agent Memory" (`workspace/`)
    from "Infrastructure Configuration". Introduce a `METACLAW_CONFIG` directory that distributes
    Telegraf `.conf` files and Grafana `dashboards.json` files across the cluster.
*   **[~] Build Services API:** Develop a generic MetaClaw Services API (Python/REST)
    that allows OpenClaw projects to interact with 'the TSDB', 'the Logger', or 'the Collector' without
    knowing the underlying provider implementation. Initial stubs (`lib/services.py`, `lib/devices.py`) have been drafted.
*   **[TODO] Expand Centralized Device Registry:**
    Expand `./lib/services.py` and `./lib/devices.py` to handle all physical hardware registry tracking. Refactor edge scripts (like `features/kasa/bin/power_kasa.py`) to query this unified library instead of manually opening and parsing the raw `hardware.json` mapping files on every execution loop.
*   **[TODO] Implement Version Control Service (`vcs`):** Provision the `gitea` provider
    to allow non-technical users to securely version-control their `workspace` and `METACLAW_CONFIG`
    repositories locally, removing the dependency on external GitHub configurations.
