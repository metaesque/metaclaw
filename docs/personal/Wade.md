# OpenClaw Architectural Topology & Maintenance Ledger

This document serves as the structural source of truth for the local OpenClaw multi-agent ecosystem. It defines the physical hardware distribution, the hierarchical agent topology, and the strict operational interdependencies required to prevent architectural regression.

## 1. Hardware Configuration & Split-Location Topology

The current environment operates on a remote, split-location architecture. The human operator is nomadic, while the heavy compute cluster is anchored to a residential broadband connection.

### Location A: The Nomadic Client (Ford Transit Van)
- **Environment:** Ford Transit van traversing North America (Alberta/BC/Nevada).
- **Power:** LiFePO4 battery bank, legacy AGM, and solar array yield.
- **Uplink:** Starlink Satellite (approx. 160 Mbps down / 20 Mbps up).
- **Hardware:** 15-inch Apple MacBook Air (M4 chip), 16 GB RAM, 256GB SSD, running macOS Sequoia Version 15.7.5 (24G624). Purchased in Buenos Aires, Argentina in April 2026 (~$1750 USD).
- **Role:** The primary client interface. Accesses the cluster remotely via Tailscale.

### Location B: The AI Farm (Parent's Basement)
- **Environment:** Climate-controlled residential basement in Lethbridge, Alberta. AC grid power.
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

---

## 2. Dynamic Hardware & Asset Ledger

This section tracks every computing and electrical asset in the ecosystem. OpenClaw uses this ledger to maintain programmatic reality-alignment regarding physical constraints.

### 2.1 Host & Compute Assets

#### Nomadic Client Laptop
* **Date Bought:** April 2026
* **Price Spent:** $1,750.00 USD
* **Title/Description:** 15-inch Apple MacBook Air M4
* **Source URL:** N/A (Purchased retail in Buenos Aires, Argentina)
* **Detailed Specifications:** Apple M4 Architecture, 16GB Unified Memory, 256GB NVMe SSD, running macOS Sequoia Version 15.7.5 (24G624).

#### Node 01 (Control Plane Server)
* **Date Bought:** Mid-2026
* **Price Spent:** ~$399.99 - $519.00 USD
* **Title/Description:** GMKtec Gaming Mini PC K8 Plus AMD Ryzen 7 8845HS Desktop Computer Dual NIC 2.5G
* **Source URL:** https://www.amazon.com/dp/B0DHNTW3H6
* **Detailed Specifications:** AMD Ryzen 7 8845HS (8 Cores, 16 Threads, Base 3.8GHz, Boost up to 5.1GHz, 16MB L3 Cache, 45W TDP). 32GB DDR5 Dual-Channel RAM. 1TB PCIe 4.0 M.2 2280 NVMe SSD. Dual 2.5 Gbps Ethernet RJ45 ports. 1x USB4 (40Gbps/PD/DP), 2x HDMI 2.1, 1x Oculink port (PCIe 4.0 x4), Wi-Fi 6E, Bluetooth 5.2.

#### Node 02 (Compute Plane Inference Server)
* **Date Bought:** Mid-2026
* **Price Spent:** ~$1,999.99 - $2,666.99 CAD
* **Title/Description:** GMKtec EVO-X2 AI Mini PC Ryzen Al Max+ 395 Mini Gaming Computer
* **Source URL:** https://www.amazon.ca/dp/B0F53MLYQ6
* **Detailed Specifications:** AMD Ryzen AI Max+ 395 (16 Cores, 32 Threads, up to 5.1GHz). Integrated AMD Radeon 8060S GPU (40 Compute Units). 128GB LPDDR5X 8000MHz (16GB x 8 configuration) Unified Memory layout. 2TB PCIe 4.0 NVMe SSD. Dual 2.5G LAN ports, WiFi 7, Bluetooth 5.4, USB4 interfaces, SD Card Reader 4.0, support for Quad Screen 8K Displays.

### 2.2 Network & Uplink Assets

#### Core Farm Network Switch
* **Date Bought:** Mid-2026
* **Price Spent:** ~$270.00 CAD
* **Title/Description:** Binardat 8 Port 10 Gigabit Managed Switch Metal Small Network Switch
* **Source URL:** https://www.amazon.ca/dp/B0DQ77BS64
* **Detailed Specifications:** Layer 3 Web Managed engine. 160Gbps total backplane switching bandwidth. Physical layout: 4x 10G RJ45 Copper Ethernet ports + 4x 10G SFP+ Fiber interface cages. Native NBASE-T auto-negotiation support (10G/5G/2.5G/1G/100M).

#### Satellite Mobile Uplink Kit
* **Date Bought:** 2022-07-19
* **Price Spent:** $650.92 USD (All-in, including initial $100 deposit)
* **Title/Description:** Starlink Standard Actuated Kit
* **Source URL:** https://starlink.com/account/orders
* **Detailed Specifications:** Circular parabolic antenna array with motorized mechanical actuation alignment. Operational power consumption range: 50W - 75W continuous draw. Dual-band 3x3 MIMO Wi-Fi 5 router base. Outdoor rated (IP54).

### 2.3 Mobile Power & Storage Assets (Van Footprint)

#### Core LiFePO4 Battery Bank
* **Date Bought:** 2026-06-03
* **Price Spent:** $499.09 USD
* **Title/Description:** Renogy 12V 100Ah Lithium LiFePO4 Deep Cycle Battery with Bluetooth
* **Source URL:** https://www.amazon.com/dp/B00S1QCK94
* **Detailed Specifications:** 12.8V Nominal Voltage, 100Ah Rated Capacity (1280Wh total energy). Integrated Bluetooth 5.0 module for local app readout. 2000+ deep cycles at 80% DOD execution boundaries. Built-in smart Battery Management System (BMS) protection loops. Weight: ~26 lbs.

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
* **Price Spent:** $60.00 USD
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

## 3. Equipment Acquisition Pipeline

This section catalogs pending hardware evaluations required to stabilize global operations across nomadic and static deployments.

### 3.1 Tier 1/2 Basement Safety Upgrades
* **Target Equipment:** Uninterruptible Power Supply (UPS) for Location B.
* **Functional Mandate:** Must support pure sine wave AC output to safely protect the Binardat 10G backplane, GMKtec K8 Plus, and GMKtec EVO-X2 against grid voltage fluctuations or micro-blackouts in Lethbridge, AB. Must support an open network management interface (e.g., USB HID or SNMP via NUT/apcupsd) so that `sre_incident` can track grid drop events and cleanly command the OpenClaw database to run a safe `VACUUM` and graceful system shutdown before battery depletion.

### 3.2 Van Electrical Power Infrastructure Expansion
* **Target Equipment:** Pure Sine Wave High-Output Inverter (1500W - 2000W).
* **Functional Mandate:** Required to scale van operations as mobile computing, tool usage, and logistics workloads grow. The current Potek 750W modified sine wave inverter is heavily constrained and insufficient for expanded multi-modality audio/video processing stations or heavy inductive tool draw.

### 3.3 Nomadic Satellite Uplink Optimization
* **Target Equipment:** Next-Generation Flat/Starlink Mini Array Hardware.
* **Functional Mandate:** Under evaluation by the `sre_bandwidth` and `sre_power` agents to reduce setup times, minimize power profiles, and remove the mechanical failure vectors of the legacy 2022 Actuated dish while tracking WAN performance across varying geographical terrains.

---

## 4. Agent Hierarchy & Topologies
*(Historical records andvertical structures continue exactly as parsed in preceding turns...)*

