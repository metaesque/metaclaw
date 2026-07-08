# OpenClaw Architectural Topology & Maintenance Ledger

This document serves as the structural source of truth for the local OpenClaw multi-agent ecosystem. It defines the physical hardware distribution, the hierarchical agent topology, and the strict operational interdependencies required to prevent architectural regression.

## 1. Hardware Configuration & Split-Location Topology

The current environment operates on a remote, split-location architecture. The human operator is nomadic, while the heavy compute cluster is anchored to a residential broadband connection.

### Location A: The Nomadic Client (Ford Transit Van)
- **Environment:** Ford Transit van traversing North America (Alberta/BC/Nevada).
- **Power:** LiFePO4 battery bank and solar yield.
- **Uplink:** Starlink Satellite (approx. 160 Mbps down / 20 Mbps up).
- **Hardware:** 15-inch Apple MacBook Air (M4 chip), 16 GB RAM, 256GB SSD, running macOS Sequoia Version 15.7.5 (24G624). Purchased in Buenos Aires, Argentina in April 2026 (~$1750 USD).
- **Role:** The primary client interface. Accesses the cluster remotely via Tailscale.

### Location B: The AI Farm (Parent's Basement)
- **Environment:** Climate-controlled residential basement. AC grid power.
- **Uplink:** Shaw HFC Broadband (approx. 600 Mbps down / 200 Mbps up).
- **Networking:** Shaw Router -> Binardat 8-Port 10G Managed Switch (4x 10G RJ45, 4x 10G SFP+, 160Gbps Bandwidth, L3 Web Managed) -> Compute/Control Nodes.

**Node 01: GMKtec K8 Plus (The Edge Gateway)**
- **Specs:** AMD Ryzen 7 8845HS (8C/16T, up to 5.1GHz), 32GB DDR5 RAM, 1TB PCIe 4.0 M.2 SSD. Features Dual 2.5G NICs, HDMI 2.1, USB4, and Oculink. (Purchased via Amazon US).
- **Role:** The Control Plane. Handles core infrastructure (PostgreSQL/pgvector, Redis, LiteLLM, VictoriaLogs) and the OpenClaw Gateway.
- **Resident LLM:** `gemma4:e4b` (acting as the fast-path Predictive Judge and simple-model executor).

**Node 02: GMKtec EVO-X2 (The Inference Engine)**
- **Specs:** AMD Ryzen AI Max+ 395 (16C/32T, up to 5.1GHz) with AMD Radeon 8060S (40 Cores) iGPU. 128GB LPDDR5X 8000MHz Quad Channel RAM, 2TB PCIe 4.0 SSD. Features Dual 2.5G LAN, WiFi 7, BT 5.4, USB4, and Quad Screen 8K Display support. (Purchased via Amazon Canada).
- **Role:** The Compute Plane. Handles deep reasoning, DAG generation, complex coding, and heavy creative asset generation.
- **Resident LLMs (Hot):**
  - `qwen-3-32b` (4-bit, ~20GB VRAM). The primary Orchestrator, coding, and `medium-model` / `complex-model` engine.
- **Resident LLMs (Cold-Swappable):**
  - `flux-1-dev` (FP16, ~24GB VRAM) for SFW imagery.
  - `pony-diffusion-v6-xl` (FP16, ~12GB VRAM) for NSFW imagery.
  - `local-video-diffusion` and `local-audio-pipeline`.

### The Fallback Gateway (Cloud)
- **External API:** `google/gemini-3.1-pro`.
- **Role:** Fulfills `frontier-model` requests for extreme context windows or zero-shot architecture design that exceeds the EVO-X2's local capabilities.

## 2. Agent Hierarchy & Topologies

The system enforces a strict Vertical Command Structure to prevent routing loops and context dilution. Agents do not communicate peer-to-peer across domains.

### 2.1 The Global Routing Layer
- **`clow_judge` (Router) [K8 Plus | gemma4:e4b]:** Intent classifier. Protects token budgets via continuous thresholding into 4 tiers (`simple`, `medium`, `complex`, `frontier`).
- **`orchestrator` (Strategic Planner) [EVO-X2 | qwen-3-32b]:** Global DAG generator. Delegates exclusively to the 7 Team Leads.

### 2.2 The Software Team
*Domain: Engineering, architecture, testing, and deployment.*
- **Lead:** `system_architect` [EVO-X2 | qwen-3-32b or Gemini] - System design and local DAG delegation.
- **Worker:** `lead_developer` [EVO-X2 | qwen-3-32b] - Application code and script execution.
- **Worker:** `qa_engineer` [EVO-X2 | qwen-3-32b] - Test harness generation and edge-case execution.
- **Worker:** `security_auditor` [K8 Plus | gemma4:e4b] - CVE scanning and log/cost analysis.
- **Worker:** `project_manager` [K8 Plus | gemma4:e4b] - Sprint tracking and requirement validation.

### 2.3 The Research Team
*Domain: OSINT, financial modeling, and ambient technology scanning.*
- **Lead:** `report_synthesizer` [EVO-X2 | qwen-3-32b or Gemini] - Briefing compilation and local DAG delegation.
- **Worker:** `web_scout` [EVO-X2 | qwen-3-32b] - Large-context web scraping and HTML extraction.
- **Worker:** `financial_quant` [EVO-X2 | qwen-3-32b] - Python-based math and multi-currency analysis.
- **Worker:** `horizon_scanner` [EVO-X2 | qwen-3-32b] - Academic paper and patent tracking.
- **Worker:** `logistics_concierge` [K8 Plus | gemma4:e4b] - Physical-world routing, visa, and hardware sourcing.

### 2.4 The Self (Modeling) Team
*Domain: Psychological sandbox, relational topologies, and biometric evaluation (Eudaimonia/Hedonia/Health).*
- **Lead:** `self_lead` [EVO-X2 | qwen-3-32b or Gemini] - Models strict data pipelines and local DAG delegation.
- **Worker:** `psychological_council` [EVO-X2 | Gemini] - Secular humanist mixture-of-experts synthesis.
- **Worker:** `human_simulator` [EVO-X2 | qwen-3-32b] - Ephemeral sandbox twin for testing interventions.
- **Worker:** `socratic_mirror` [EVO-X2 | qwen-3-32b] - Cognitive friction and logical fallacy detection.
- **Worker:** `relational_sociologist` [EVO-X2 | qwen-3-32b] - Non-monogamous network graph topology analysis.
- **Worker:** `data_archivist` [K8 Plus | gemma4:e4b] - Air-gapped biometric and digital exhaust retrieval.
- **Worker:** `action_integrator` [K8 Plus | gemma4:e4b] - Routine translation and calendar blocking.

### 2.5 The Media Team
*Domain: Creative asset generation and VRAM cold-swap execution.*
- **Lead:** `media_producer` [EVO-X2 | qwen-3-32b] - Modality delegation and hardware concurrency limits.
- **Worker:** `sfw_designer` [EVO-X2 | flux-1-dev] - Diagram and graphic layout rendering.
- **Worker:** `nsfw_artist` [EVO-X2 | pony-v6-xl] - Uncensored anatomical character styling.
- **Worker:** `video_director` [EVO-X2 | local-video] - Temporal synthesis and motion vectors.
- **Worker:** `audio_engineer` [EVO-X2 | local-audio] - Voice cloning and text-to-speech.

### 2.6 The SRE (Grid) Team
*Domain: Cluster stability, distributed network resilience, and system administration.*
- **Lead:** `sre_lead` [EVO-X2 | qwen-3-32b] - Disaster recovery and blameless post-mortems.
- **Worker:** `sre_incident` [EVO-X2 | qwen-3-32b] - Emergency graceful degradation protocols.
- **Worker:** `sre_power` [EVO-X2 | qwen-3-32b] - Remote monitoring of the Transit van's solar/battery telemetry.
- **Worker:** `sre_telemetry` [K8 Plus | gemma4:e4b] - Log parsing and memory leak detection.
- **Worker:** `sre_network` [K8 Plus | gemma4:e4b] - Tailscale ACLs and remote tunnel latency to the van.
- **Worker:** `sre_db` [K8 Plus | gemma4:e4b] - PostgreSQL/pgvector vacuuming and index health.
- **Worker:** `sre_thermal` [K8 Plus | gemma4:e4b] - Temperature throttling and hardware protection for the basement nodes.
- **Worker:** `sre_storage` [K8 Plus | gemma4:e4b] - NVMe wear tracking and volume pruning.
- **Worker:** `sre_sysadmin` [EVO-X2 | qwen-3-32b] - Host-level shell commands and file manipulation.

## 3. Structural Interdependencies (Maintenance Ledger)

As the OpenClaw environment evolves, failing to update paired files will result in architectural breakdown, routing loops, or VRAM exhaustion. Adhere to the following cascade rules:

### 3.1 Adding or Removing a Subordinate Agent
If you add a new worker (e.g., `sre_security`) to an existing team:
1. **Update the Team Lead's System Prompt:** Modify `workspace/agents/<team>/<lead>/SOUL.md`. You must explicitly add the new agent to the `LOCAL DELEGATION MATRIX` section. The Team Lead cannot route to agents it does not know exist.
2. **Update YAML & LiteLLM:** Ensure the `model:` specified in the new agent's YAML utilizes a conceptual tier (`simple-model`, etc.) registered in the Gateway proxy.

### 3.2 Adding a New Team (Domain)
If you create a completely new team branch:
1. **Update the Global Orchestrator:** Modify `workspace/agents/orchestrator/SOUL.md`. You must append the new Team Lead to the `HIERARCHICAL DELEGATION MATRIX`.
2. **Update the Escalation Protocol:** You must update the `THE ESCALATION PROTOCOL` section inside the `SOUL.md` of **every existing Team Lead** so they know they can escalate tasks requiring the new team's specific capabilities.

### 3.3 Upgrading Hardware (Changing VRAM/RAM capacity)
If you add a new host or upgrade memory constraints:
1. **Update Telemetry Memory:** Modify `workspace/agents/sre/telemetry/MEMORY.md` so the Warden agent knows the new absolute limits before throwing an Out-Of-Memory alert.
2. **Update Producer Memory:** Modify `workspace/agents/media/producer/MEMORY.md`. If you gain enough VRAM to keep Flux and Qwen hot simultaneously, you must remove the strict concurrency/cold-swap limits from the Producer's configuration.

