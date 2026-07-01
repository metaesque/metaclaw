# OpenClaw Architectural Topology & Maintenance Ledger

This document serves as the structural source of truth for the local OpenClaw multi-agent ecosystem. It defines the physical hardware constraints, the hierarchical agent topology, and the strict operational interdependencies required to prevent architectural regression.

## 1. Hardware Configuration & LLM Allocation

The current environment operates on a two-node distributed cluster, constrained by the power and thermal realities of a Ford Transit van traversing North America (Alberta/BC/Nevada).

### Node 01: GMKtec K8 Plus (The Edge Gateway)
- **Specs:** 32GB RAM, 1TB SSD. CPU-bound inference.
- **Role:** Handles core infrastructure (PostgreSQL/pgvector, Redis, LiteLLM, VictoriaLogs) and high-frequency, I/O-bound edge agents.
- **Resident LLM:** `gemma4:12b` (4-bit QAT). Remains permanently hot.

### Node 02: GMKtec EVO-X2 (The Inference Engine)
- **Specs:** 128GB LPDDR5X, 2TB SSD, Ryzen AI Max+ 395. Allocates up to 96GB of unified memory to the Radeon 8060S GPU.
- **Role:** Handles deep reasoning, DAG generation, complex coding, and heavy creative asset generation.
- **Resident LLMs (Hot):**
  - `llama4-scout-109b` (4-bit MoE, ~55GB VRAM). The primary Orchestrator and deep logic engine.
  - `qwen-3-32b` (4-bit, ~20GB VRAM). The primary coding, math, and cypher engine.
- **Resident LLMs (Cold-Swappable):**
  - `flux-1-dev` (FP16, ~24GB VRAM) for SFW imagery.
  - `pony-diffusion-v6-xl` (FP16, ~12GB VRAM) for NSFW imagery.
  - `local-video-diffusion` and `local-audio-pipeline`.

### The Fallback Gateway
- **External API:** `google/gemini-3.1-pro`.
- **Role:** Exclusively reserved for extreme context windows (>100K tokens) or frontier-level zero-shot architecture design that exceeds local VRAM capacity.

## 2. Agent Hierarchy & Topologies

The system enforces a strict Vertical Command Structure to prevent routing loops and context dilution. Agents do not communicate peer-to-peer across domains.

### 2.1 The Global Routing Layer
- **`clow_judge` (Router) [K8 Plus | gemma4:12b]:** Intent classifier. Protects frontier token budgets via continuous thresholding.
- **`orchestrator` (Strategic Planner) [EVO-X2 | llama4-109b]:** Global DAG generator. Delegates exclusively to the 5 Team Leads.

### 2.2 The Software Team
*Domain: Engineering, architecture, testing, and deployment.*
- **Lead:** `system_architect` [EVO-X2 | llama4-109b] - System design and local DAG delegation.
- **Worker:** `lead_developer` [EVO-X2 | qwen-32b] - Application code and script execution.
- **Worker:** `qa_engineer` [EVO-X2 | qwen-32b] - Test harness generation and edge-case execution.
- **Worker:** `security_auditor` [K8 Plus | gemma4:12b] - CVE scanning and log/cost analysis.
- **Worker:** `project_manager` [K8 Plus | gemma4:12b] - Sprint tracking and requirement validation.

### 2.3 The Research Team
*Domain: OSINT, financial modeling, and ambient technology scanning.*
- **Lead:** `report_synthesizer` [EVO-X2 | llama4-109b] - Briefing compilation and local DAG delegation.
- **Worker:** `web_scout` [EVO-X2 | qwen-32b] - Large-context web scraping and HTML extraction.
- **Worker:** `financial_quant` [EVO-X2 | qwen-32b] - Python-based math and multi-currency analysis.
- **Worker:** `horizon_scanner` [EVO-X2 | llama4-109b] - Academic paper and patent tracking.
- **Worker:** `logistics_concierge` [K8 Plus | gemma4:12b] - Physical-world routing, visa, and hardware sourcing.

### 2.4 The Self (Modeling) Team
*Domain: Psychological sandbox, relational topologies, and biometric evaluation (Eudaimonia/Hedonia/Health).*
- **Lead:** `self_lead` [EVO-X2 | llama4-109b] - Models strict data pipelines and local DAG delegation.
- **Worker:** `psychological_council` [EVO-X2 | llama4-109b] - Secular humanist mixture-of-experts synthesis.
- **Worker:** `human_simulator` [EVO-X2 | qwen-32b] - Ephemeral sandbox twin for testing interventions.
- **Worker:** `socratic_mirror` [EVO-X2 | llama4-109b] - Cognitive friction and logical fallacy detection.
- **Worker:** `relational_sociologist` [EVO-X2 | qwen-32b] - Non-monogamous network graph topology analysis.
- **Worker:** `data_archivist` [K8 Plus | gemma4:12b] - Air-gapped biometric and digital exhaust retrieval.
- **Worker:** `action_integrator` [K8 Plus | gemma4:12b] - Routine translation and calendar blocking.

### 2.5 The Media Team
*Domain: Creative asset generation and VRAM cold-swap execution.*
- **Lead:** `media_producer` [EVO-X2 | llama4-109b] - Modality delegation and hardware concurrency limits.
- **Worker:** `sfw_designer` [EVO-X2 | flux-1-dev] - Diagram and graphic layout rendering.
- **Worker:** `nsfw_artist` [EVO-X2 | pony-v6-xl] - Uncensored anatomical character styling.
- **Worker:** `video_director` [EVO-X2 | local-video] - Temporal synthesis and motion vectors.
- **Worker:** `audio_engineer` [EVO-X2 | local-audio] - Voice cloning and text-to-speech.

### 2.6 The SRE (Grid) Team
*Domain: Cluster stability, van-based power budgeting, and network resilience.*
- **Lead:** `sre_lead` [EVO-X2 | llama4-109b] - Disaster recovery and blameless post-mortems.
- **Worker:** `sre_incident` [EVO-X2 | llama4-109b] - Emergency graceful degradation protocols.
- **Worker:** `sre_power` [EVO-X2 | qwen-32b] - Solar yield and LiFePO4 battery degradation math.
- **Worker:** `sre_telemetry` [K8 Plus | gemma4:12b] - Log parsing and memory leak detection.
- **Worker:** `sre_network` [K8 Plus | gemma4:12b] - Tailscale ACLs and WebSocket latency checking.
- **Worker:** `sre_db` [K8 Plus | gemma4:12b] - PostgreSQL/pgvector vacuuming and index health.
- **Worker:** `sre_thermal` [K8 Plus | gemma4:12b] - Temperature throttling and hardware protection.
- **Worker:** `sre_storage` [K8 Plus | gemma4:12b] - NVMe wear tracking and volume pruning.
- **Worker:** `sre_bandwidth` [K8 Plus | gemma4:12b] - Starlink telemetry and background task throttling.

## 3. Structural Interdependencies (Maintenance Ledger)

As the OpenClaw environment evolves, failing to update paired files will result in architectural breakdown, routing loops, or VRAM exhaustion. Adhere to the following cascade rules:

### 3.1 Adding or Removing a Subordinate Agent
If you add a new worker (e.g., `sre_security`) to an existing team:
1. **Update the Team Lead's System Prompt:** Modify `workspace/agents/<team>/<lead>.yaml`. You must explicitly add the new agent to the `LOCAL DELEGATION MATRIX` section. The Team Lead cannot route to agents it does not know exist.
2. **Update LiteLLM:** Ensure the `model:` specified in the new agent's YAML is registered in the Gateway proxy.

### 3.2 Adding a New Team (Domain)
If you create a completely new team branch (e.g., `finance_team`):
1. **Update the Global Orchestrator:** Modify `workspace/agents/orchestrator.yaml`. You must append the new Team Lead to the `HIERARCHICAL DELEGATION MATRIX`.
2. **Update the Escalation Protocol:** You must update the `THE ESCALATION PROTOCOL` section inside the `system_prompt` of **every existing Team Lead** (Architect, Synthesizer, Producer, Self Lead, SRE Lead) so they know they can escalate tasks requiring the new team's specific capabilities.

### 3.3 Upgrading Hardware (Changing VRAM/RAM capacity)
If you add a new host or upgrade memory constraints:
1. **Model Assignments:** Audit every `model:` parameter across all `.yaml` files. Shift models between the K8 Plus (Gateway) and EVO-X2 (Inference) to optimize load.
2. **Update Telemetry Memory:** Modify `workspace/agents/sre/telemetry/MEMORY.md` so the Warden agent knows the new absolute limits before throwing an Out-Of-Memory alert.
3. **Update Producer Memory:** Modify `workspace/agents/media/producer/MEMORY.md`. If you gain enough VRAM to keep Flux and Llama 4 hot simultaneously, you must remove the strict concurrency/cold-swap limits from the Producer's configuration.

### 3.4 The Escalation Protocol Dependency
The ability for teams to request cross-domain tasks relies on a specific script: `bin/handle_escalation.py`. 
- If you modify the JSON schema that Team Leads use to request help (e.g., changing `"required_capability"` to `"target_domain"` in the YAML files), you **must** also rewrite the Python script's JSON parser, or the Global Orchestrator will silently drop the escalation request.
