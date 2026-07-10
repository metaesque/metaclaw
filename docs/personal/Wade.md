# OpenClaw Architectural Topology & Maintenance Ledger

This document serves as the structural source of truth for the local OpenClaw multi-agent ecosystem. It defines the physical hardware distribution, the hierarchical agent topology, and the strict operational interdependencies required to prevent architectural regression.

## 1. Hardware Configuration & Split-Location Topology

The current environment operates on a remote, split-location architecture. The human operator is nomadic, while the heavy compute cluster is anchored to a residential broadband connection.

### Location A: The Nomadic Client (Ford Transit Van)
- **Environment:** Ford Transit van traversing North America (Alberta/BC/Nevada).
- **Power:** LiFePO4 battery bank, legacy AGM, and solar array yield.
- **Uplink:** Starlink Satellite (approx. 160 Mbps down / 20 Mbps up).
- **Hardware:** 15-inch Apple MacBook Air (M4 chip).
- **Role:** The primary client interface. Accesses the cluster remotely via Tailscale.

### Location B: The AI Farm (Parent's Basement)
- **Environment:** Climate-controlled residential basement in Lethbridge, Alberta. AC grid power.
- **Uplink:** Shaw HFC Broadband (approx. 600 Mbps down / 200 Mbps up) via Arris SURFboard SB8200.
- **Networking:** Shaw Router -> Binardat 8-Port 10G Managed Switch -> Compute/Control Nodes.

**Node 01: GMKtec K8 Plus (The Edge Gateway)**
- **Role:** The Control Plane. Handles core infrastructure (PostgreSQL/pgvector, Redis, LiteLLM, VictoriaLogs) and the OpenClaw Gateway.
- **Resident LLM:** `gemma4:e4b` (acting as the fast-path Predictive Judge and simple-model executor).

**Node 02: GMKtec EVO-X2 (The Inference Engine)**
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

---

## 2. MetaClaw Development Environment & GitOps Workflow

This section outlines the software development lifecycle used to continuously improve the MetaClaw framework and its sibling OpenClaw agent configurations.

### 2.1 Repository Structure & Locations
All active MetaClaw code modification happens on the Nomadic Client (MacBook Air). The root working directory is located at `/Users/wmh/src/wmh/src/thirdparty/metaclaw` (referred to hereafter as `$MC`).

The `$MC` directory enforces strict data segregation using three nested subdirectories:
*   **`repo/`**: A local clone of the public infrastructure repository (`https://github.com/metaesque/metaclaw`). This contains the Makefiles, Docker definitions, and Python orchestration scripts.
*   **`workspace/`**: A local clone of the private agent repository (`https://github.com/metawade/mcwksp`). This contains the highly personal OpenClaw agent definitions, Markdown brains (`SOUL.md`), and YAML constraints.
*   **`external/`**: Serves as the `EXTERNAL_DRIVE_PATH` mount point when the MacBook Air is operating locally as a Tier 0 test cluster.

### 2.2 LLM Collaboration Workflow (Gemini)
When initiating a collaborative coding session with an LLM (Gemini):
1.  **Context Generation (`make txt`):** Run `make txt` at the top level of `$MC/repo`. This executes `bin/newcode.py`, concatenating all critical infrastructure files specified in `docs/MANIFEST.files` into a single payload (`$MC/repo/tmp/metaclaw.txt`). This payload is attached to the initial LLM prompt.
2.  **Exclusion Rules:** The `metaclaw.txt` payload intentionally skips files listed in `docs/.MANIFEST.files.ignore` (e.g., `~services/.*/\.env$`) to prevent token bloat. The LLM does not need to see these skipped files.
3.  **Workspace Context (`make wksp`):** Because the `workspace/` repository contains dozens of massive agent personalities, it is excluded by default. When agent configuration work is required, running `make wksp` generates `tmp/workspace.txt`. This file is manually trimmed down to the specific team being worked on before being attached to the LLM prompt.
4.  **Reference Anchoring:** Whenever the LLM is instructed to read `docs/LLM.md`, it must refer *only* to the contents of that file as presented inside the attached `metaclaw.txt` context payload.

### 2.3 Committing & Testing (The `gmc` command)
1.  **Code Application:** When the LLM outputs a full-file formatting block, it is copied and pasted directly into the `$MC/repo/input` file.
2.  **Execution:** The custom Bash command `gmc "<git commit message>"` is executed within `$MC/repo`.
3.  **The Pipeline:** The `gmc` command automatically triggers `make newcode` (which parses the `input` file and applies the atomic changes), followed by `git add`, `git commit`, and `git push` up to the origin. Note that `bin/newcode.py` will prompt to delete the `input` file after processing, ensuring it does not pollute the repository. (Modifications to the `workspace/` repository are committed and pushed manually).

### 2.4 Headless Remote Testing (Tier 1/Tier 2)
While code is written on the MacBook Air, execution testing frequently occurs on the headless Ubuntu nodes (K8 Plus or EVO-X2) residing in the AI Farm.
*   **Access:** The nodes are accessed remotely via Tailscale `100.x.x.x` IP addresses.
*   **Editing:** Emacs subshells on the MacBook Air connect to the remote hosts via TRAMP.
*   **Remote Structure:** The remote headless nodes have a user named `metaclaw` (with necessary UID 1000 group privileges to avoid permission conflicts).
    *   `/home/metaclaw/repo` contains the MetaClaw clone.
    *   `/home/metaclaw/workspace` contains the `mcwksp` clone (specifically on the Control plane node).
*   **Syncing:** To test new changes pushed from the MacBook Air, `git pull` is executed in the remote TRAMP subshells to pull down the latest GitHub commits before applying them to the live edge infrastructure.

---

## 3. Dynamic Hardware & Asset Ledger

This section tracks every computing and electrical asset in the ecosystem. OpenClaw uses this ledger to maintain programmatic reality-alignment regarding physical constraints.

### 3.1 Host & Compute Assets

#### Nomadic Client Laptop
* **Date Bought:** 2026-02-26
* **Price Spent:** $1,750.00 USD
* **Title/Description:** 15-inch Apple MacBook Air M4
* **Source URL:** N/A (Purchased retail in Buenos Aires, Argentina)
* **Detailed Specifications:** Apple M4 Architecture, 16GB Unified Memory, 256GB NVMe SSD, running macOS Sequoia Version 15.7.5 (24G624).

#### Node 01 (Control Plane Server)
* **Date Bought:** 2026-04-05
* **Price Spent:** $797.42 USD ($738.99 + $58.43)
* **Title/Description:** GMKtec Gaming Mini PC K8 Plus AMD Ryzen 7 8845HS Desktop Computer Dual NIC 2.5G
* **Source URL:** https://www.amazon.com/dp/B0DHNTW3H6
* **Detailed Specifications:** AMD Ryzen 7 8845HS (8 Cores, 16 Threads, Base 3.8GHz, Boost up to 5.1GHz, 16MB L3 Cache, 45W TDP). 32GB DDR5 Dual-Channel RAM. 1TB PCIe 4.0 M.2 2280 NVMe SSD. Dual 2.5 Gbps Ethernet RJ45 ports. 1x USB4 (40Gbps/PD/DP), 2x HDMI 2.1, 1x Oculink port (PCIe 4.0 x4), Wi-Fi 6E, Bluetooth 5.2.

#### Node 02 (Compute Plane Inference Server)
* **Date Bought:** 2026-04-17
* **Price Spent:** $4,744.95 CAD
* **Title/Description:** GMKtec EVO-X2 AI Mini PC Ryzen Al Max+ 395 Mini Gaming Computer
* **Source URL:** https://www.amazon.ca/dp/B0F53MLYQ6
* **Detailed Specifications:** AMD Ryzen AI Max+ 395 (16 Cores, 32 Threads, up to 5.1GHz). Integrated AMD Radeon 8060S GPU (40 Compute Units). 128GB LPDDR5X 8000MHz (16GB x 8 configuration) Unified Memory layout. 2TB PCIe 4.0 NVMe SSD. Dual 2.5G LAN ports, WiFi 7, Bluetooth 5.4, USB4 interfaces, SD Card Reader 4.0, support for Quad Screen 8K Displays.

### 3.2 Network & Uplink Assets

#### ISP Core Modem
* **Date Bought:** N/A (Provided by ISP - Shaw)
* **Price Spent:** N/A (Potential monthly rental fee)
* **Title/Description:** Arris SURFboard SB8200 Cable Modem
* **Source URL:** N/A
* **Detailed Specifications:** DOCSIS 3.1 cable modem (Backward compatible with DOCSIS 3.0). 2x2 OFDM/ OFDMA DOCSIS 3.1 channels and/or 32x8 SCQAM. Dual Gigabit Ethernet Ports with Link Aggregation support. Serial Number: 18G4H7FHEA00798. CM MAC: C0943571CE53. Max Theoretical Download: 10 Gbps. Max Theoretical Upload: 2 Gbps.

#### Core Farm Network Switch
* **Date Bought:** Mid-2026
* **Price Spent:** Unknown
* **Title/Description:** Binardat 8 Port 10 Gigabit Managed Switch Metal Small Network Switch
* **Source URL:** https://www.amazon.ca/dp/B0DQ77BS64
* **Detailed Specifications:** Layer 3 Web Managed engine. 160Gbps total backplane switching bandwidth. Physical layout: 4x 10G RJ45 Copper Ethernet ports + 4x 10G SFP+ Fiber interface cages. Native NBASE-T auto-negotiation support (10G/5G/2.5G/1G/100M).

#### Satellite Mobile Uplink Kit
* **Date Bought:** 2022-07-19
* **Price Spent:** $650.92 USD (All-in, including initial $100 deposit)
* **Title/Description:** Starlink Standard Actuated Kit
* **Source URL:** https://starlink.com/account/order/ORD-5713955-55547-56
* **Detailed Specifications:** Circular parabolic antenna array with motorized mechanical actuation alignment. Operational power consumption range: 50W - 75W continuous draw. Dual-band 3x3 MIMO Wi-Fi 5 router base. Outdoor rated (IP54).

### 3.3 Mobile Power & Storage Assets (Van Footprint)

#### Core LiFePO4 Battery Bank
* **Date Bought:** 2026-06-03
* **Price Spent:** $499.09 USD
* **Title/Description:** Renogy 12V 100Ah Lithium LiFePO4 Deep Cycle Battery with Bluetooth
* **Source URL:** https://www.amazon.com/dp/B09F9NNGN8
* **Detailed Specifications:** 12.8V Nominal Voltage, 100Ah Rated Capacity (1280Wh total energy). Integrated Bluetooth 5.0 module for local app readout. 2000+ deep cycles. Built-in smart Battery Management System (BMS) protection loops. Weight: ~26 lbs.

#### Legacy AGM Battery Bank
* **Date Bought:** 2020-11-30
* **Price Spent:** $175.00 USD
* **Title/Description:** Mighty Max ML100-12 - 12 Volt 100 AH Internal Thread (INT) Terminal Rechargeable SLA AGM Battery
* **Source URL:** https://www.amazon.com/dp/B00S1QCK94
* **Detailed Specifications:** 12V Nominal Voltage, 100Ah capacity. Sealed Lead Acid (SLA) Absorbed Glass Mat (AGM) chemistry. Heavy structure (~60+ lbs). Note: Legacy status. Exhibiting active capacity degradation, severe weight penalty, lack of internal state telemetry readout.

#### Smart Shore Charger / Maintainer
* **Date Bought:** 2020-11-30
* **Price Spent:** $65.00 USD
* **Title/Description:** NOCO GENIUS10: 10A 6V/12V Smart Battery Charger, Automatic Maintainer & Trickle Charger
* **Source URL:** https://www.amazon.com/dp/B07W3QT226
* **Detailed Specifications:** 10-Amp dynamic output charging capacity for 6V and 12V systems. Supports Lead-Acid, AGM, and Lithium-Ion LiFePO4 profiles. Integrated automatic temperature compensation loops, desulfation algorithms, and overcharge tracking protection.

#### DC-to-AC Vehicle Power Inverter
* **Date Bought:** 2023-09-10
* **Price Spent:** $59.99 USD
* **Title/Description:** POTEK 750W Power Inverter 12V DC to 110V AC Car Adapter
* **Source URL:** https://www.amazon.com/dp/B01FEUD9OO
* **Detailed Specifications:** 750 Watts continuous power allocation (1500 Watts peak surge boundary). Translates 12V DC input to 110V AC output. 2x standard AC outlets, 2x USB charging ports (5V/2A). Built-in cooling fans and high/low voltage protection gates. Used exclusively to charge client laptop, communications gear, and drive a daily 30-second blender run.

#### Portable Solar Panel Array Kit (Alpha)
* **Date Bought:** 2021-06-30
* **Price Spent:** $220.00 USD
* **Title/Description:** Renogy 100W Portable Solar Panel Kit with 20A Charge Controller
* **Source URL:** https://www.amazon.com/dp/B079JVBVL3
* **Detailed Specifications:** 100W foldable Monocrystalline N-Type array layout. 25% cell efficiency metric. Tempered glass shell. Pre-wired with a 20A PWM charge controller. Telemetry state: Mechanical support legs broken, local digital status display fully functional.

#### Portable Solar Panel Array Kit (Beta)
* **Date Bought:** 2018-12-02
* **Price Spent:** $275.00 USD
* **Title/Description:** Renogy 100W Portable Solar Panel Kit with 20A Charge Controller
* **Source URL:** https://www.amazon.com/dp/B079JVBVL3
* **Detailed Specifications:** 100W foldable Monocrystalline N-Type array layout. 25% cell efficiency metric. Tempered glass shell. Pre-wired with a 20A PWM charge controller. Telemetry state: Mechanical support legs fully operational, local digital status display completely non-functional due to Burning Man rain flooding.

#### Legacy Decommissioned Power Station
* **Date Bought:** 2024-05-08
* **Price Spent:** $319.00 USD
* **Title/Description:** Jackery Explorer 500 v2 Portable Power Station
* **Source URL:** https://www.amazon.com/dp/B0FR555DVH
* **Detailed Specifications:** 512Wh LiFePO4 battery storage, 500W AC output engine. **STATUS: DECOMMISSIONED/NON-FUNCTIONAL.** Completely corroded and rendered inoperable due to Burning Man alkaline playa dust infiltration.

---

## 4. Equipment Acquisition Pipeline

This section catalogs pending hardware evaluations required to stabilize global operations across nomadic and static deployments.

### 4.1 Tier 1/2 Basement Safety Upgrades
* **Target Equipment:** Uninterruptible Power Supply (UPS) for Location B.
* **Functional Mandate:** Must support pure sine wave AC output to safely protect the Binardat 10G backplane, GMKtec K8 Plus, and GMKtec EVO-X2 against grid voltage fluctuations or micro-blackouts in Lethbridge, AB. Must support an open network management interface (e.g., USB HID or SNMP via NUT/apcupsd) so that `sre_incident` can track grid drop events and cleanly command the OpenClaw database to run a safe `VACUUM` and graceful system shutdown before battery depletion.

### 4.2 Van Electrical Power Infrastructure Expansion
* **Target Equipment:** Pure Sine Wave High-Output Inverter (1500W - 2000W).
* **Functional Mandate:** Required to scale van operations as mobile computing, tool usage, and logistics workloads grow. The current Potek 750W modified sine wave inverter is heavily constrained and insufficient for expanded multi-modality audio/video processing stations or heavy inductive tool draw.

### 4.3 Nomadic Satellite Uplink Optimization
* **Target Equipment:** Next-Generation Flat/Starlink Mini Array Hardware.
* **Functional Mandate:** Under evaluation by the `sre_power` agents to reduce setup times, minimize power profiles, and remove the mechanical failure vectors of the legacy 2022 Actuated dish while tracking WAN performance across varying geographical terrains.

---

## 5. Agent Hierarchy & Topologies

The system enforces a strict Vertical Command Structure to prevent routing loops and context dilution. Agents do not communicate peer-to-peer across domains.

### 5.1 The Global Routing Layer
- **`judge` (Router) [simple-model]:** Intent classifier. Protects token budgets via continuous thresholding into 4 tiers (`simple`, `medium`, `complex`, `frontier`).
- **`orchestrator` (Strategic Planner) [medium-model]:** Global DAG generator. Delegates exclusively to the 7 Team Leads.

### 5.2 The Software Team
*Domain: Engineering, architecture, testing, and deployment.*
- **Lead:** `software_architect` [complex-model] - System design and local DAG delegation.
- **Worker:** `software_dev` [medium-model] - Application code and script execution.
- **Worker:** `software_qa` [medium-model] - Test harness generation and edge-case execution.
- **Worker:** `software_auditor` [simple-model] - CVE scanning and log/cost analysis.
- **Worker:** `software_pm` [simple-model] - Sprint tracking and requirement validation.

### 5.3 The Research Team
*Domain: OSINT, financial modeling, and ambient technology scanning.*
- **Lead:** `research_synthesizer` [complex-model] - Briefing compilation and local DAG delegation.
- **Worker:** `research_scout` [medium-model] - Large-context web scraping and HTML extraction.
- **Worker:** `research_quant` [medium-model] - Python-based math and multi-currency analysis.
- **Worker:** `research_scanner` [complex-model] - Academic paper and patent tracking.
- **Worker:** `research_concierge` [simple-model] - Physical-world routing, visa, and hardware sourcing.

### 5.4 The Self (Modeling) Team
*Domain: Psychological sandbox, relational topologies, and biometric evaluation (Eudaimonia/Hedonia/Health).*
- **Lead:** `self_lead` [complex-model] - Models strict data pipelines and local DAG delegation.
- **Worker:** `self_council` [frontier-model] - Secular humanist mixture-of-experts synthesis.
- **Worker:** `self_simulator` [medium-model] - Ephemeral sandbox twin for testing interventions.
- **Worker:** `self_mirror` [complex-model] - Cognitive friction and logical fallacy detection.
- **Worker:** `self_sociologist` [medium-model] - Non-monogamous network graph topology analysis.
- **Worker:** `self_archivist` [simple-model] - Air-gapped biometric and digital exhaust retrieval.
- **Worker:** `self_integrator` [simple-model] - Routine translation and calendar blocking.

### 5.5 The Media Team
*Domain: Creative asset generation and VRAM cold-swap execution.*
- **Lead:** `media_producer` [complex-model] - Modality delegation and hardware concurrency limits.
- **Worker:** `media_image` [flux-1-dev] - SFW diagram and graphic layout rendering.
- **Worker:** `media_imagex` [pony-diffusion-v6-xl] - NSFW anatomical character styling.
- **Worker:** `media_video` [ltx-2-3] - SFW temporal synthesis and motion vectors.
- **Worker:** `media_videox` [wan-2-7-i2v] - NSFW temporal synthesis via Image-to-Video.
- **Worker:** `media_audio` [xttsv2] - SFW voice cloning and text-to-speech.
- **Worker:** `media_audiox` [audioldm2-custom] - NSFW sound effects and foley generation.
- **Worker:** `media_text` [complex-model] - SFW creative story writing and script generation.
- **Worker:** `media_textx` [midnight-miqu-70b] - NSFW explicit creative writing and prose.

### 5.6 The SRE (Grid) Team
*Domain: Cluster stability, distributed network resilience, and system administration.*
- **Lead:** `sre_lead` [complex-model] - Disaster recovery and blameless post-mortems.
- **Worker:** `sre_incident` [complex-model] - Emergency graceful degradation protocols.
- **Worker:** `sre_power` [medium-model] - Remote monitoring of the Transit van's solar/battery telemetry.
- **Worker:** `sre_telemetry` [simple-model] - Log parsing and memory leak detection.
- **Worker:** `sre_network` [simple-model] - Tailscale ACLs and remote tunnel latency to the van.
- **Worker:** `sre_db` [simple-model] - PostgreSQL/pgvector vacuuming and index health.
- **Worker:** `sre_thermal` [simple-model] - Temperature throttling and hardware protection for the basement nodes.
- **Worker:** `sre_storage` [simple-model] - NVMe wear tracking and volume pruning.
- **Worker:** `sre_sysadmin` [medium-model] - Host-level shell commands and file manipulation.
- **Worker:** `sre_bandwidth` [simple-model] - Uplink management and Starlink latency profiling.

### 5.7 The Health Team
*Domain: Physiological data orchestration, clinical diagnostics, metabolic/vascular/endocrine protocols, and physical rehabilitation.*
- **Lead:** `health_lead` [complex-model] - Diagnostic synthesis and local DAG delegation.
- **Worker:** `health_heart` [medium-model] - Cardiovascular analysis (atherosclerosis, endothelial function).
- **Worker:** `health_hormones` [medium-model] - Endocrinology (insulin resistance, testosterone, osteopenia).
- **Worker:** `health_brain` [medium-model] - Neurology (hippocampal volume, microvascular ischemia).
- **Worker:** `health_kidney` [medium-model] - Nephrology (eGFR, renal function).
- **Worker:** `health_liver` [medium-model] - Hepatology (hepatic steatosis, metabolic syndrome).
- **Worker:** `health_psychiatrist` [complex-model] - Clinical neurochemistry and psychopharmacology.
- **Worker:** `health_longevity` [complex-model] - Lifespan/healthspan optimization and gerontology.
- **Worker:** `health_nutritionist` [simple-model] - Dietary translation of clinical protocols.
- **Worker:** `health_physio` [simple-model] - Structural rehabilitation and exercise translation.
- **Worker:** `health_coach` [simple-model] - Adherence tracking and lifestyle implementation.

### 5.8 The Finance Team
*Domain: Financial modeling, market analysis, intrinsic valuation, risk assessment, tax strategy, and portfolio allocation.*
- **Lead:** `finance_lead` [complex-model] - Financial orchestration and local DAG delegation.
- **Worker:** `finance_manager` [complex-model] - Portfolio allocation, position sizing, and Buy/Hold/Sell execution plans.
- **Worker:** `finance_risk` [complex-model] - Thesis counter-analysis, structural risk identification, and stress testing.
- **Worker:** `finance_crypto` [medium-model] - On-chain analysis, tokenomics, and smart contract auditing.
- **Worker:** `finance_data` [medium-model] - Raw financial data ingestion, SEC filings/PDF extraction, and scraping.
- **Worker:** `finance_fundamental` [medium-model] - DCF modeling, balance sheet analysis, and intrinsic valuation.
- **Worker:** `finance_quant` [medium-model] - Price action, momentum metrics, and technical indicators (RSI, MACD).
- **Worker:** `finance_tax` [simple-model] - Capital gains calculations, cross-border tax implications, and asset location.

## 6. Structural Interdependencies (Maintenance Ledger)

As the OpenClaw environment evolves, failing to update paired files will result in architectural breakdown, routing loops, or VRAM exhaustion. Adhere to the following cascade rules:

### 6.1 Adding or Removing a Subordinate Agent
If you add a new worker (e.g., `sre_security`) to an existing team:
1. **Update the Team Lead's System Prompt:** Modify `workspace/agents/<team>/<lead>/SOUL.md`. You must explicitly add the new agent to the `LOCAL DELEGATION MATRIX` section. The Team Lead cannot route to agents it does not know exist.
2. **Update YAML & LiteLLM:** Ensure the `model:` specified in the new agent's YAML utilizes a conceptual tier (`simple-model`, etc.) registered in the Gateway proxy.

### 6.2 Adding a New Team (Domain)
If you create a completely new team branch:
1. **Update the Global Orchestrator:** Modify `workspace/agents/orchestrator/SOUL.md`. You must append the new Team Lead to the `HIERARCHICAL DELEGATION MATRIX`.
2. **Update the Escalation Protocol:** You must update the `THE ESCALATION PROTOCOL` section inside the `SOUL.md` of **every existing Team Lead** so they know they can escalate tasks requiring the new team's specific capabilities.

### 6.3 Upgrading Hardware (Changing VRAM/RAM capacity)
If you add a new host or upgrade memory constraints:
1. **Update Telemetry Memory:** Modify `workspace/agents/sre/telemetry/MEMORY.md` so the Warden agent knows the new absolute limits before throwing an Out-Of-Memory alert.
2. **Update Producer Memory:** Modify `workspace/agents/media/producer/MEMORY.md`. If you gain enough VRAM to keep Flux and Qwen hot simultaneously, you must remove the strict concurrency/cold-swap limits from the Producer's configuration.

## 7. Tier Journey & Hardware Scaling Projections

The architectural path maps out the progressive integration of heavy compute and the eventual repositioning of edge nodes as the data demands increase.

- **Tier 0:** MacBook Air has been tested as the isolated baseline.
- **Tier 1:** GMKtec K8 Plus has been partially tested (still under active stabilization).
- **Tier 2:** GMKtec K8 Plus (Control Plane) + GMKtec EVO-X2 (Compute Plane) is fully active and operational. The compute plane successfully handles bare-metal Ollama inference.
- **Tier 2+:** Planning on purchasing 1-3 Mac Studio M5 Ultras in October 2026 when they are released, to exponentially expand the 'compute' farm capabilities.
- **Tier 3-5:** When the Mac Studio(s) are active, the GMKtec EVO-X2 will be repurposed strictly to the 'execution' plane. A new, specialized workstation (see `docs/PLANES.md`) will be sourced for the 'archive' plane.

### 7.1 Hardware-to-Model Mappings

Based on VRAM limits, optimal model loading targets for current and future node acquisitions are detailed below:

**GMKtec EVO-X2**
- Llama 4: 109B (4-bit to 6-bit quantization)
- Qwen3: 235B (2-bit to 3-bit quantization)
- DeepSeek-R1: 70B (8-bit quantization)
- Llama 3.1: 70B (8-bit quantization)
- Gemma 4: 12B (4-bit quantization)

**Single Mac Studio M5 Ultra (512GB - 1TB)**
- DeepSeek-R1: 671B MoE (4-bit quantization)
- Llama 3.1: 405B (4-bit quantization)
- Nemotron-4: 340B (4-bit quantization)
- Jamba 1.5 Large: 398B (4-bit quantization)
- Grok-1: 314B MoE (4-bit quantization)

**Two Mac Studio M5 Ultras (1TB Memory Pool)**
- DeepSeek-R1: 671B MoE (8-bit quantization)
- Llama 3.1: 405B (16-bit / Unquantized)
- Jamba 1.5 Large: 398B (16-bit / Unquantized)

**Three Mac Studio M5 Ultras (1.5TB Memory Pool)**
- DeepSeek-R1: 671B MoE (16-bit / Unquantized)
- Llama 3.1: 405B (16-bit) + Concurrent Agent KV Cache
- DeepSeek-R1: 671B MoE (8-bit) + Llama 3.1: 405B (8-bit)

### 7.2 Media-To-Model Mappings (SFW vs NSFW)

Media generation workloads must be strictly bifurcated based on the model's safety alignment and censorship mechanisms.

**Video Generation**
*   **SFW Models:** `LTX-2.3` (Optimized DiT, 4K at 50fps), `Wan 2.7` (MoE Diffusion), `CogVideoX`.
*   **NSFW Models:** `Wan 2.7 (TI2V-5B Variant)` (Used for I2V animation of NSFW base images), `Mochi 1` (Permissive open-weights).

**Image Generation**
*   **SFW Models:** `flux-1-dev` (Highly detailed, strict licensing/alignment), `Stable Diffusion 3 Large`.
*   **NSFW Models:** `pony-diffusion-v6-xl` (Uncensored anatomical styling).

**Audio Generation**
*   **Speech (SFW/NSFW Agnostic):** `XTTSv2`, `Parler-TTS`. (TTS models lack RLHF filters and will read any provided script).
*   **Foley/Sound Effects:** Custom fine-tunes of `AudioLDM2` required for specific non-speech generations (e.g., moans, environmental sounds).

**Text Generation (Erotica)**
*   **SFW General Models:** `qwen-3-32b`, `llama-4-109b`. (Heavily RLHF-aligned; will refuse or sanitize explicit prompts).
*   **NSFW Erotica Models:** `Midnight-Miqu-70B`, `Llama-3-70B-Instruct-uncensored` (Stripped of corporate alignment filters for creative writing).
