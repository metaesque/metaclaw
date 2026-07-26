# MetaClaw Architecture Roadmap

This document outlines the strategic evolution of the MetaClaw framework, tracking technical debt, planned features, and architectural pivots identified during deployment testing.

## Phase 1: Foundation (Current)
*   [x] Establish the `openclaw-network` mesh.
*   [x] Implement `profile.json` dynamic orchestration.
*   [x] Establish Tier 0 (Minilith) and Tier 2 (Compute Farm) baseline topologies.
*   [x] Implement LiteLLM fallback chains (`medium-model` -> `gemini-2.5-flash`).
*   [x] Distribute workloads via Tailscale SSH integration using native `subprocess`.

## Hardware Optimization (Pending Actions)
*   **[TODO] Reclaim UMA Frame Buffer RAM:**
    The GMKtec K8 Plus currently reserves ~3.78GB of RAM for the integrated Radeon 780M graphics (UMA Frame Buffer). Because the node runs headless (no display), this memory is wasted and hidden from the OS.
    **Action Required:** Reboot the K8 Plus, enter the BIOS (`Del` or `F2`), navigate to **Advanced -> AMD CBS -> NBIO Common Options -> GFX Configuration -> UMA Frame buffer Size**, and change it to `Auto` or `512MB`. This will free up RAM for Docker services, while the GPU continues to dynamically allocate inference memory via GTT.

## Phase 2: Distributed State & Observability (Upcoming)
*   **[TODO] Distributed Logging (VictoriaLogs & Fluent Bit):**
    Currently, VictoriaLogs only aggregates Docker JSON logs from the local `control` node. We need to explicitly configure `fluent-bit.conf` to tail bare-metal log files (e.g., `services/runners/ollama/ollama.log`) and deploy lightweight Fluent Bit forwarders to all remote `compute` and `execution` nodes to push telemetry back to the centralized `ACTIVE_LOGGER_HOST`.
*   **[TODO] Overcoming `num_ctx` Defaults:**
    While models like `llama4-scout` have massive context limits, Ollama defaults API requests to 2048 tokens. OpenClaw Orchestrator prompts routinely exceed 7500 tokens. We must implement a centralized mechanism (via LiteLLM config or OpenClaw routing patches) to explicitly inject a high `num_ctx` (e.g., 16384) to prevent context truncation and subsequent cloud fallback.

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
*   **[TODO] Multi-Tenant Priority Proxying (LiteLLM):**
    Implement Virtual Key management and rate limiting within the local LiteLLM proxy to allow external users (friends) to access the Compute Plane. Ensure the proxy maintains a priority queue that privileges internal owner prompts to prevent VRAM eviction of hot models during heavy external load.

## Phase 5: Templating Engine Migration (Jinja2)
*   **[TODO] Transition .env Overrides to Jinja2 Compilation:**
    The current `.env.template` injection system requires complex, rigid Python logic (`orchestrate.py`) to map specific variables. We must replace this by implementing a `bin/compile_templates.py` engine that utilizes Jinja2 `.j2` template files. This will allow declarative rendering of Compose and Config files directly from `profile.json` node parameters (e.g., `{% if hardware.gpu_detected == "AMD APU" %}`), removing the need for error-prone `change_me_to_` prompt bypasses and global overrides.

## Phase 6: Arena-Driven Model Routing
*   **[TODO] Deprecate Rigid 'Middle Reasoning' DAG:**
    Move away from hardcoding specific models (`complex-model`, `medium-model`) in agent YAML definitions. The current multi-hop DAG approach introduces latency and arbitrary model assignments.
*   **[TODO] Implement LMArena.ai Taxonomy Mapping:**
    Utilize the `bin/fetch_arena.py` script to scrape the live Gradio JSON state from LMArena. Modify agent YAMLs to include an `arena_category` parameter (e.g., `Chat/Text/Legal & Government`). The Orchestrator will act as a single-shot Intent Classifier, passing the prompt to the appropriate agent, while MetaClaw's orchestration engine dynamically binds the #1 ranked ELO model for that category to the agent executing the task.
