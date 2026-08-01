# OpenClaw Architectural Topology & Maintenance Ledger

This document serves as the structural source of truth for the local OpenClaw
multi-agent ecosystem. It defines the physical hardware distribution, the
hierarchical agent topology, and the strict operational interdependencies
required to prevent architectural regression.

## Hardware Configuration & Split-Location Topology

The current environment operates on a remote, split-location architecture. The
human operator is nomadic, while the heavy compute cluster is anchored to a
residential broadband connection.

### Location A: The Nomadic Client (Ford Transit Van)

- **Environment:** Ford Transit van traversing North America (Alberta/BC/Nevada).
- **Power:** LiFePO4 battery bank, legacy AGM, and solar array yield.
- **Uplink:** Starlink Satellite (approx. 160 Mbps down / 20 Mbps up).
- **Hardware:** 15-inch Apple MacBook Air (M4 chip).
- **Role:** The primary client interface. Accesses the cluster remotely via
  Tailscale.

### Location B: The AI Farm (Parent's Basement)

- **Environment:** Climate-controlled residential basement in Lethbridge,
  Alberta. AC grid power.
- **Uplink:** Shaw HFC Broadband (approx. 600 Mbps down / 200 Mbps up) via Arris SURFboard SB8200.
- **Networking:** Shaw Router -> Binardat 8-Port 10G Managed Switch ->
  Compute/Control Nodes.

**Node 01: GMKtec K8 Plus (The Edge Gateway)**

- **Role:** The Control Plane. Handles core infrastructure (PostgreSQL/pgvector,
  Redis, LiteLLM, VictoriaLogs) and the OpenClaw Gateway.
- **Resident LLM:** `gemma4:e4b` (acting as the fast-path Predictive Judge and
  simple-model executor).

**Node 02: GMKtec EVO-X2 (The Inference Engine)**

- **Role:** The Compute Plane. Handles deep reasoning, DAG generation, complex
  coding, and heavy creative asset generation.

- **Resident LLMs (Hot):**
  - `ingu627/llama4-scout-q4:109b` (4-bit, ~65GB footprint). The primary text
    orchestration, coding, and `complex-model` / `reasoning-model` engine.

- **Resident LLMs (Cold-Swappable):**
  - `flux-1-dev` (FP16, ~24GB VRAM) for SFW imagery.
  - `pony-diffusion-v6-xl` (FP16, ~12GB VRAM) for NSFW imagery.
  - `local-video-diffusion` and `local-audio-pipeline`.

### The Fallback Gateway (Cloud)

- **External API:** `google/gemini-3.1-pro`.

- **Role:** Fulfills `frontier-model` requests for extreme context windows or
  zero-shot architecture design that exceeds the EVO-X2's local capabilities.

## MetaClaw Development Environment & GitOps Workflow

This section outlines the software development lifecycle used to continuously
improve the MetaClaw framework and its sibling OpenClaw agent configurations.

### Repository Structure & Locations

All active MetaClaw code modification happens on the Nomadic Client (MacBook
Air). The root working directory is located at
`/Users/wmh/src/wmh/src/thirdparty/metaclaw` (referred to hereafter as `$MC`).

The `$MC` directory enforces strict data segregation using three nested subdirectories:
*   **`repo/`**: A local clone of the public infrastructure repository
    (`https://github.com/metaesque/metaclaw`). This contains the Makefiles,
    Docker definitions, and Python orchestration scripts.
*   **`workspace/`**: A local clone of the private agent repository
    (`https://github.com/metawade/mcwksp`). This contains the highly personal
    OpenClaw agent definitions, Markdown brains (`SOUL.md`), and YAML
    constraints.
*   **`external/`**: Serves as the `EXTERNAL_DRIVE_PATH` mount point when the
    MacBook Air is operating locally as a Tier 0 test cluster.

### LLM Collaboration Workflow (Gemini)

When initiating a collaborative coding session with an LLM (Gemini):

1.  **Context Generation (`make txt`):** Run `make txt` at the top level of
    `$MC/repo`. This executes `bin/newcode.py`, concatenating all critical
     infrastructure files specified in `docs/MANIFEST.files` into a single
     payload (`$MC/repo/tmp/metaclaw.txt`). This payload is attached to the
     initial LLM prompt.
2.  **Exclusion Rules:** The `metaclaw.txt` payload intentionally skips files
    listed in `docs/.MANIFEST.files.ignore` (e.g., `~services/.*/\.env$`) to
    prevent token bloat. The LLM does not need to see these skipped files.
3.  **Workspace Context (`make wksp`):** Because the `workspace/` repository
    contains dozens of massive agent personalities, it is excluded by default.
    When agent configuration work is required, running `make wksp` generates
    `tmp/workspace.txt`. This file is manually trimmed down to the specific team
    being worked on before being attached to the LLM prompt.
4.  **Reference Anchoring:** Whenever the LLM is instructed to read
    `docs/LLM.md`, it must refer *only* to the contents of that file as
    presented inside the attached `metaclaw.txt` context payload.

### Committing & Testing (The `gmc` command)

1.  **Code Application:** When the LLM outputs a full-file formatting block, it
    is copied and pasted directly into the `$MC/repo/input` file.
2.  **Execution:** The custom Bash command `gmc "<git commit message>"` is
    executed within `$MC/repo`.
3.  **The Pipeline:** The `gmc` command automatically triggers `make newcode`
    (which parses the `input` file and applies the atomic changes), followed by
    `git add`, `git commit`, and `git push` up to the origin. Note that
    `bin/newcode.py` will prompt to delete the `input` file after processing,
    ensuring it does not pollute the repository. (Modifications to the
    `workspace/` repository are committed and pushed manually).

### Headless Remote Testing (Tier 1/Tier 2)

While code is written on the MacBook Air, execution testing frequently occurs on
the headless Ubuntu nodes (K8 Plus or EVO-X2) residing in the AI Farm.

*   **Access:** The nodes are accessed remotely via Tailscale `100.x.x.x` IP
    addresses.
*   **Editing:** Emacs subshells on the MacBook Air connect to the remote hosts
    via TRAMP.
*   **Remote Structure:** The remote headless nodes have a user named `metaclaw`
    (with necessary UID 1000 group privileges to avoid permission conflicts).
    *   `/home/metaclaw/repo` contains the MetaClaw clone.
    *   `/home/metaclaw/workspace` contains the `mcwksp` clone (specifically on
        the Control plane node).
*   **Syncing:** To test new changes pushed from the MacBook Air, `git pull`
    is executed in the remote TRAMP subshells to pull down the latest GitHub
    commits before applying them to the live edge infrastructure.

## Dynamic Hardware & Asset Ledger

This section tracks every computing and electrical asset in the ecosystem.
OpenClaw uses this ledger to maintain programmatic reality-alignment regarding
physical constraints.

### Host & Compute Assets

#### Nomadic Client Laptop

* **Date Bought:** 2026-02-26
* **Price Spent:** $1,750.00 USD
* **Title/Description:** 15-inch Apple MacBook Air M4
* **Source URL:** N/A (Purchased retail in Buenos Aires, Argentina)
* **Detailed Specifications:** Apple M4 Architecture, 16GB Unified Memory,
  256GB NVMe SSD, running macOS Sequoia Version 15.7.5 (24G624).

#### Node 01 (Control Plane Server)

* **Date Bought:** 2026-04-05
* **Price Spent:** $797.42 USD ($738.99 + $58.43)
* **Title/Description:** GMKtec Gaming Mini PC K8 Plus AMD Ryzen 7 8845HS
  Desktop Computer Dual NIC 2.5G
* **Source URL:** https://www.amazon.com/dp/B0DHNTW3H6
* **Detailed Specifications:** AMD Ryzen 7 8845HS (8 Cores, 16 Threads, Base
  3.8GHz, Boost up to 5.1GHz, 16MB L3 Cache, 45W TDP). 32GB DDR5 Dual-Channel
  RAM. 1TB PCIe 4.0 M.2 2280 NVMe SSD. Dual 2.5 Gbps Ethernet RJ45 ports. 1x
  USB4 (40Gbps/PD/DP), 2x HDMI 2.1, 1x Oculink port (PCIe 4.0 x4), Wi-Fi 6E,
  Bluetooth 5.2.
* **VRAM:** Shared system RAM (32GB DDR5). No dedicated VRAM.
* **Memory bandwidth:** ~89.6 GB/s (Dual-channel DDR5-5600).
* **Compute Capability:** CPU only / Radeon 780M iGPU (~8 TFLOPS FP16).
* **Precision Acceleration:** None native (relies on standard CPU AVX
  instructions for INT8).
* **Interconnect:** 2.5 Gbps Ethernet.

#### Node 02 (Compute Plane Inference Server)

* **Date Bought:** 2026-04-17
* **Price Spent:** $4,744.95 CAD
* **Title/Description:** GMKtec EVO-X2 AI Mini PC Ryzen Al Max+ 395 Mini
  Gaming Computer
* **Source URL:** https://www.amazon.ca/dp/B0F53MLYQ6
* **Detailed Specifications:** AMD Ryzen AI Max+ 395 (16 Cores, 32 Threads,
  up to 5.1GHz). Integrated AMD Radeon 8060S GPU (40 Compute Units). 128GB
  LPDDR5X 8000MHz (16GB x 8 configuration) Unified Memory layout. 2TB PCIe 4.0
  NVMe SSD. Dual 2.5G LAN ports, WiFi 7, Bluetooth 5.4, USB4 interfaces, SD Card
  Reader 4.0, support for Quad Screen 8K Displays.
* **VRAM:** 128GB LPDDR5X 8000MHz Unified Memory (Up to 96GB allocatable to GPU).
* **Memory bandwidth:** 256 GB/s.
* **Compute Capability:** Radeon 8060S iGPU (~30-40 TFLOPS FP16).
* **Precision Acceleration:** Standard FP16/INT8. No native sub-INT8 hardware.
* **Interconnect:** 2.5 Gbps Ethernet (Not suitable for tensor parallelism).

#### Node 03 (Compute Plane Inference Server)

* **Date Bought:** 2026-07-16
* **Price Spent:** $5776.83 CAD all-in (included free ASUS ROG Strik 27" QHD 2K
  1440P 260Hz IPS Gaming Computer Monitor valued at $576 CAD)
* **Title/Description:** ASUS Ascent GX10 AI Supercomputer, DGX Spark, NVIDIA
  GB10 Superchip, 128GB LPDDR5x, 1TB PCIe Gen4 NVMe SSD, Wi-Fi 7 & BT5.4, DGX OS
* **Source URL:** https://www.newegg.ca/asus-ascent-gx10-mini-pc/p/N82E16859110044
* **Detailed Specifications:** NVIDIA GB10 Grace Blackwell Superchip (Arm
  v9.2-A 20-core CPU, integrated Blackwell GPU with 6144 Cores and 384 Tensor
  Cores). 128GB unified LPDDR5x memory (273 GB/s bandwidth). 1TB PCIe 4.0 NVMe
  SSD. Networking: 1x RJ45 10GbE LAN, 2x QSFP 200G ConnectX-7 SmartNIC ports.
  Wi-Fi 7, Bluetooth 5.4. Supports up to 1 PetaFLOP (FP4) AI compute. Draws up
  to 180W via 240W USB-C PD 3.1 EPR adapter.
* **VRAM:** 128GB unified LPDDR5x memory.
* **Memory bandwidth:** 273 GB/s.
* **Compute Capability:** Up to 1 PetaFLOP (FP4) via integrated Blackwell GPU
  (6144 Cores, 384 Tensor Cores).
* **Precision Acceleration:** Native hardware acceleration for FP8 and FP4 MoE
  routing.
* **Interconnect:** 200 Gbps (QSFP56 DAC). Natively scales up to 4 nodes.

#### Node 04 (Compute Plane Inference Server)

* **Date Bought:** 2026-08-06
* **Price Spent:** $5776.83 CAD (All-in pricing matched to Node 03)
* **Title/Description:** ASUS Ascent GX10 AI Supercomputer, DGX Spark, NVIDIA
  GB10 Superchip, 128GB LPDDR5x, 1TB PCIe Gen4 NVMe SSD, Wi-Fi 7 & BT5.4, DGX OS
* **Source URL:** https://www.newegg.ca/asus-ascent-gx10-mini-pc/p/N82E16859110044
* **Detailed Specifications:** NVIDIA GB10 Grace Blackwell Superchip (Arm
  v9.2-A 20-core CPU, integrated Blackwell GPU with 6144 Cores and 384 Tensor
  Cores). 128GB unified LPDDR5x memory (273 GB/s bandwidth). 1TB PCIe 4.0 NVMe
  SSD. Networking: 1x RJ45 10GbE LAN, 2x QSFP 200G ConnectX-7 SmartNIC ports.
  Wi-Fi 7, Bluetooth 5.4.
* **VRAM:** 128GB unified LPDDR5x memory.
* **Memory bandwidth:** 273 GB/s.
* **Compute Capability:** Up to 1 PetaFLOP (FP4) via integrated Blackwell GPU
  (6144 Cores, 384 Tensor Cores).
* **Precision Acceleration:** Native hardware acceleration for FP8 and FP4
  MoE routing.
* **Interconnect:** 200 Gbps (QSFP56 DAC). Natively scales up to 4 nodes.

#### Node 05 (Compute Plane Inference Server)

* **Date Bought:** 2026-10-20
* **Price Spent:** TBD
* **Title/Description:** Apple Mac Studio M5 Ultra (Projected)
* **Source URL:** TBD
* **Detailed Specifications:** Apple M5 Ultra SoC. Up to 36 CPU cores, 80 GPU cores. 96GB or 128GB Unified Memory baseline. 2TB baseline NVMe storage. Networking: 10GbE RJ45 port, multiple Thunderbolt 5 ports (120 Gbps bandwidth for RDMA inter-node tensor sharding), Wi-Fi 7, Bluetooth 6.
* **VRAM:** 96GB or 128GB Unified Memory (Projected).
* **Memory bandwidth:** 800+ GB/s (Projected).
* **Compute Capability:** ~50-80 TFLOPS (FP16) via Apple GPU.
* **Precision Acceleration:** Software quantization via MLX. Lacks native
  hardware FP4 matrix cores.
* **Interconnect:** 120 Gbps (RDMA over Thunderbolt 5). Supports up to 4 nodes
  via Exo clustering.

#### Node 06 (Compute Plane Inference Server)

* **Date Bought:** 2026-10-20
* **Price Spent:** TBD
* **Title/Description:** Apple Mac Studio M5 Ultra (Projected)
* **Source URL:** TBD
* **Detailed Specifications:** Apple M5 Ultra SoC. Up to 36 CPU cores,
  80 GPU cores. 96GB or 128GB Unified Memory baseline. 2TB baseline NVMe
  storage. Networking: 10GbE RJ45 port, multiple Thunderbolt 5 ports (120 Gbps
  bandwidth for RDMA inter-node tensor sharding), Wi-Fi 7, Bluetooth 6.
* **VRAM:** 96GB or 128GB Unified Memory (Projected).
* **Memory bandwidth:** 800+ GB/s (Projected).
* **Compute Capability:** ~50-80 TFLOPS (FP16) via Apple GPU.
* **Precision Acceleration:** Software quantization via MLX. Lacks native
  hardware FP4 matrix cores.
* **Interconnect:** 120 Gbps (RDMA over Thunderbolt 5). Supports up to 4 nodes
  via Exo clustering.

### Comparative Hardware Metrics for Local LLM Inference

| Computer Name | Price | VRAM Size | VRAM Arch. | Gb/s | TFLOPS | Acc. | Interconnect |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GMKtec K8 Plus** | [$797.42 USD](https://www.amazon.com/dp/B0DHNTW3H6) | 32GB | Shared DDR5 | ~90 | ~8 | None | 2.5 GbE |
| **GMKtec EVO-X2** | [$4,999.00 CAD](https://www.amazon.ca/GMKtec-EVO-X2-Computers-LPDDR5X-8000MHz/dp/B0F53MLYQ6) | 128GB | Unified LPDDR5x | ~256 | ~30-40 | None | 2.5 GbE |
| **AMD Ryzen AI Halo Dev Platform** | [$3,999.00 USD](https://www.pcmag.com/news/amd-ryzen-ai-halo-first-look-giant-local-ai-power-in-a-pint-sized-box) | 128GB | Unified LPDDR5x | 256 | ~30-40 | None | 10 GbE / USB-C |
| **Framework Desktop (Strix Halo)** | [$3,999.00 USD](https://www.storagereview.com/review/amd-ryzen-ai-halo-review-a-dual-os-200b-parameter-desktop-takes-on-the-dgx-spark) | 128GB | Unified LPDDR5x | 256 | ~30-40 | None | 10 GbE / USB4 |
| **Minisforum MS-S1 Max** | [$3,639.00 USD](https://store.minisforum.com/products/minisforum-ms-s1-max-mini-pc) | 128GB | Unified LPDDR5x | 256 | ~30-40 | None | Dual 10 GbE / USB4 V2 |
| **Beelink GTR9 Pro** | [$4,349.00 USD](https://www.bee-link.com/products/beelink-gtr9-pro-amd-ryzen-ai-max-395) | 128GB | Unified LPDDR5x | 256 | ~30-40 | None | Dual 10 GbE / USB4 |
| **HP Z2 Mini G1a** | [$3,039.00 USD](https://www.pcmag.com/reviews/hp-z2-mini-g1a) | 128GB | Unified LPDDR5x | 256 | ~30-40 | None | 2.5 GbE / TBT4 |
| **ASUS DGX Spark** | [$5,776.83 CAD](https://www.newegg.ca/asus-ascent-gx10-mini-pc/p/N82E16859110044) | 128GB | Unified LPDDR5x | 273 | ~1,000 (FP4) | FP8/FP4 | QSFP56 200G DAC |
| **Mac Studio M4 Max (16C/40G)** | [$3,949.00 USD](https://www.apple.com/shop/buy-mac/mac-studio) | 64GB | Unified Memory | 546 | ~30-40 | None | Thunderbolt 5 |
| **Mac Studio M3 Ultra (32C/80G)** | [$9,749.00 USD](https://www.apple.com/shop/buy-mac/mac-studio) | 96GB | Unified Memory | 800 | ~50-60 | None | Thunderbolt 4 |
| **Mac Studio M5 Ultra (Projected)** | [TBD](https://www.macworld.com/article/2973459/2026-mac-studio-m5-release-date-specs-price-rumors.html) | 96GB+ | Unified Memory | 800+ | ~50-80 | None | Thunderbolt 5 RDMA |

### Network & Uplink Assets

#### ISP Core Modem
* **Date Bought:** N/A (Provided by ISP - Shaw)
* **Price Spent:** N/A (Potential monthly rental fee)
* **Title/Description:** Arris SURFboard SB8200 Cable Modem
* **Source URL:** N/A
* **Detailed Specifications:** DOCSIS 3.1 cable modem (Backward compatible
  with DOCSIS 3.0). 2x2 OFDM/ OFDMA DOCSIS 3.1 channels and/or 32x8 SCQAM. Dual
  Gigabit Ethernet Ports with Link Aggregation support. Serial Number:
  18G4H7FHEA00798. CM MAC: C0943571CE53. Max Theoretical Download: 10 Gbps. Max
  Theoretical Upload: 2 Gbps.

#### Core Farm Network Switch
* **Date Bought:** Mid-2026
* **Price Spent:** Unknown
* **Title/Description:** Binardat 8 Port 10 Gigabit Managed Switch Metal Small
  Network Switch
* **Source URL:** https://www.amazon.ca/dp/B0DQ77BS64
* **Detailed Specifications:** Layer 3 Web Managed engine. 160Gbps total
  backplane switching bandwidth. Physical layout: 4x 10G RJ45 Copper Ethernet
  ports + 4x 10G SFP+ Fiber interface cages. Native NBASE-T auto-negotiation
  support (10G/5G/2.5G/1G/100M).

#### Mac Management Network Switch
* **Date Bought:** 2026-10-20
* **Price Spent:** $112.00 CAD
* **Title/Description:** YuanLey 6 Port 10G Ethernet Switch Unmanaged
* **Source URL:** https://www.amazon.ca/Port-Unmanaged-RJ45-Compatible-YuanLey/dp/B0F13DYZ8K
* **Detailed Specifications:** 4 x 2.5G Base-T Ports, 2 x 10Gb RJ45 Ports.
  Compatible with 100/1000/2500Mbps, Metal Fanless, VLAN support. Used strictly for management traffic.

#### Kasa Smart Plug Power Strip HS300 (Strip 1)
* **Date Bought:** 2023-06-01
* **Price Spent:** $46.99 USD
* **Title/Description:** Kasa Smart Plug Power Strip HS300, Surge Protector
  with 6 Individually Controlled Smart Outlets and 3 USB Ports, Works with Alexa
  & Google Home, No Hub Required , White
* **Detailed Specifications:** 6 Individually controlled smart outlets, 3 USB
  ports. Built-in surge protection. Maximum physical load: 15A / 1800W. Features
  per-outlet energy monitoring (emeter) accessible via local network API.

#### Kasa Smart Plug Power Strip HS300 (Strip 2)
* **Date Bought:** 2026-07-30
* **Price Spent:** $101.07 CAD
* **Title/Description:** Kasa Smart Plug Power Strip HS300, Surge Protector with 6 Individually Controlled Smart Outlets and 3 USB Ports
* **Source URL:** https://www.walmart.ca/en/ip/Kasa-Smart-Plug-Power-Strip-HS300-Surge-Protector-6-Individually-Controlled-Outlets-3-USB-Ports-Works-Alexa-Google-Home-No-Hub-Required-White/34XV3645UCJM
* **Detailed Specifications:** 6 Individually controlled smart outlets, 3 USB ports. Built-in surge protection. Maximum physical load: 15A / 1800W. Features per-outlet energy monitoring (emeter) accessible via local network API.

#### Core Farm UPS
* **Date Bought:** 2026-07-22
* **Price Spent:** $293.00 CAD
* **Title/Description:** CyberPower CP1500PFCLCD PFC Sinewave UPS System,
  1500VA/1000W, 12 Outlets, AVR, Mini Tower, Black
* **Source URL:** https://www.amazon.ca/CyberPower-CP1500PFCLCD-Sinewave-Outlets-Mini-Tower/dp/B00429N19W
* **Detailed Specifications:** 1500VA / 1000W output capacity. Pure Sine Wave
  output (compatible with Active PFC power supplies). 12 NEMA 5-15R Outlets (6
  battery-backed & surge protected, 6 surge protected only). Automatic Voltage
  Regulation (AVR). Includes USB data port for NUT server integration.

#### SFP+ to RJ45 Transceiver (x2)
* **Date Bought:** 2026-07-22
* **Price Spent:** $210.00 CAD ($105.00 each)
* **Title/Description:** Mikrotik S+RJ10 10Gbps Ethernet Module for MikroTik
  Devices with SFP+ Ports, Up to 200m over RJ45, Active/Passive Cooling
  Compatible
* **Source URL:** https://www.amazon.ca/Mikrotik-S-RJ10-MikroTik/dp/B078SNK1MY
* **Detailed Specifications:** 10GBASE-T Copper Transceiver. Converts SFP+ cage
  to standard RJ45 port. Operates at 10Mbps/100Mbps/1Gbps/2.5Gbps/5Gbps/10Gbps.
  Maximum cable distance: 30m on Cat6a. Premium thermal throttling mitigation
  over generic brands.

#### DGX Spark Interconnect Cable
* **Date Bought:** 2026-07-23
* **Price Spent:** $204.00 CAD
* **Title/Description:** TRANSUTON 200G QSFP56 to QSFP56 PAM4 DAC Cable
  Ethernet Passive Direct Attach Copper Twinax Cable Compatible with
  NVIDIA/Mellanox MCP1650-V00AE30 (0.5m / 1.64ft)
* **Source URL:** https://www.amazon.ca/TRANSUTON-Ethernet-Compatible-Mellanox-MCP1650-V00AE30/dp/B0FX57YZXR
* **Detailed Specifications:** 0.5-meter passive Direct Attach Copper cable
  with integrated Mellanox EEPROM signatures to bypass vendor-lock.

#### Core Farm Ethernet Cabling
* **Date Bought:** 2026-07-23
* **Price Spent:** $37.00 CAD
* **Title/Description:** GearIT Cat 6 Ethernet Cable 5 ft (10-Pack) - Cat6
  Patch Cable, Network Cable, Internet Cable - Blue 5 Feet
* **Source URL:** https://www.amazon.ca/dp/B00D8N6UQ4
* **Detailed Specifications:** 10-pack of 5-foot Category 6 stranded copper
  patch cables. Supports 10 Gigabit Ethernet (10GBASE-T) over short distances up
  to 55 meters. Unshielded Twisted Pair (UTP) design with RJ45 connectors.

### Network Topology

**Power Architecture & Load Constraints**

The entire system runs off a single bedroom wall circuit capped at 15A / 1800W.

1. **Wall Outlet (Receptacle 1):** Plugs directly into the CyberPower UPS.

   - *Constraint:* The UPS battery-backed inverter is hard-limited to **1000W**.
     If the simultaneous hardware draw exceeds 1000W, the UPS will sound an
     alarm and immediately cut power to protect itself, crashing the farm.

2. **UPS Battery-Backed Outlets:**

   - Kasa HS300 Power Strip #1.
   - Kasa HS300 Power Strip #2.

3. **Kasa HS300 Strip #1:**

   - Node 01 (GMKtec K8 Plus) — ~45W
   - Node 02 (GMKtec EVO-X2) — ~100W
   - Node 03 (DGX Spark #1) — ~180W max
   - Node 04 (DGX Spark #2) — ~180W max
   - Arris SURFboard Cable Modem — ~15W

4. **Kasa HS300 Strip #2:**

   - Node 05 (Mac Studio M5 Ultra #1) — ~150W max
   - Node 06 (Mac Studio M5 Ultra #2) — ~150W max
   - Binardat 10Gb Switch — ~15W
   - YuanLey Management Switch — ~10W

**Ethernet Cabling Architecture (Management & Basic API)**

- **WAN Uplink:** Arris Modem connects to Binardat Switch (SFP+ Port 5) using
  a **GearIT Cat6 Cable** plugged into a **MikroTik S+RJ10 Transceiver**.

- **Core Fabric (Binardat Switch RJ45):**
   - RJ45 Port 1 -> **GearIT Cat6 Cable** -> Node 01 (GMKtec K8 Plus).
   - RJ45 Port 2 -> **GearIT Cat6 Cable** -> Node 02 (GMKtec EVO-X2).
   - RJ45 Port 3 -> **GearIT Cat6 Cable** -> Node 03 (DGX Spark #1).
   - RJ45 Port 4 -> **GearIT Cat6 Cable** -> Node 04 (DGX Spark #2).

- **Mac Management (YuanLey Switch):**
   - Binardat SFP+ Port 6 -> **MikroTik S+RJ10 Transceiver** -> **GearIT Cat6 Cable** -> YuanLey 10G RJ45 Port 1 (Uplink).
   - YuanLey 10G RJ45 Port 2 -> **GearIT Cat6 Cable** -> Node 05 (Mac Studio M5 Ultra #1).
   - YuanLey 2.5G RJ45 Port 1 -> **GearIT Cat6 Cable** -> Node 06 (Mac Studio M5 Ultra #2).

**High-Speed Tensor Parallel Fabrics (Bypassing Ethernet)**

- **DGX Spark Fabric:** Node 03 and Node 04 are directly connected port-to-port
  using the **0.5m TRANSUTON 200G QSFP56 DAC (MCP1650-V00AE30 compatible)**.
  This plugs into one of the ConnectX-7 ports on the back of each Spark.

- **Mac Studio Fabric:** Node 05 and Node 06 are directly daisy-chained using a
  dedicated **Thunderbolt 5 cable** (purchased separately from Apple) to handle
  all RDMA inference traffic between the Macs.

**HARDWARE CAPABILITY OVERRIDE:**

Apple Silicon Mac Studios (M3/M4/M5 running macOS 26.2+) strictly support direct
peer-to-peer RDMA over Thunderbolt 5. The Exo 1.0 clustering framework utilizes
this protocol to bypass Ethernet entirely, enabling native unified memory
pooling and tensor sharding across up to four direct-cabled Macs. This
Thunderbolt RDMA fabric achieves near-linear scaling for dense LLMs and
sub-two-second TTFT for massive Mixture of Experts models. You are strictly
forbidden from asserting that Macs cannot be clustered or that they must rely on
traditional Ethernet topologies for distributed inference.

**HARDWARE CAPABILITY OVERRIDE:**

NVIDIA DGX Spark / GB10 nodes natively support clustering of up to **four**
nodes for distributed inference. A two-node topology leverages a single 200G
QSFP56 Direct Attach Copper (DAC) cable connected point-to-point between their
ConnectX-7 NICs. A three-node topology functions as a direct-attach ring
requiring three cables. Scaling to four nodes requires a 200GbE RoCE-capable
QSFP switch. You are strictly forbidden from asserting that DGX Sparks are
hard-limited to a two-node maximum for tensor parallel distributed inference.

### Future Purchases

The following hardware has been sourced and mapped into the topology, but still
needs to be formally purchased:

- 1x ASUS Ascent DGX Spark (Node 04)
- 1x TRANSUTON 200G QSFP56 DAC (0.5m)
- 1x YuanLey 6 Port 10G/2.5G Ethernet Switch
- 2x Apple Mac Studio M5 Ultra (Node 05 and Node 06)
- 1x Apple Thunderbolt 5 Pro Cable (for chaining Mac Studios)
- 2x MikroTik S+RJ10 10Gbps Ethernet Modules
- 1x CyberPower CP1500PFCLCD UPS
- 1x Kasa HS300 Smart Power Strip
- 1x GearIT Cat 6 Ethernet Cable 5 ft (10-Pack)

### Mobile Power & Storage Assets (Van Footprint)

#### Core LiFePO4 Battery Bank

* **Date Bought:** 2026-06-03
* **Price Spent:** $499.09 USD
* **Title/Description:** Renogy 12V 100Ah Lithium LiFePO4 Deep Cycle Battery
  with Bluetooth
* **Source URL:** https://www.amazon.com/dp/B09F9NNGN8
* **Detailed Specifications:** 12.8V Nominal Voltage, 100Ah Rated Capacity
  (1280Wh total energy). Integrated Bluetooth 5.0 module for local app readout.
  2000+ deep cycles. Built-in smart Battery Management System (BMS) protection
  loops. Weight: ~26 lbs.

#### Legacy AGM Battery Bank

* **Date Bought:** 2020-11-30
* **Price Spent:** $175.00 USD
* **Title/Description:** Mighty Max ML100-12 - 12 Volt 100 AH Internal Thread
  (INT) Terminal Rechargeable SLA AGM Battery
* **Source URL:** https://www.amazon.com/dp/B00S1QCK94
* **Detailed Specifications:** 12V Nominal Voltage, 100Ah capacity. Sealed
  Lead Acid (SLA) Absorbed Glass Mat (AGM) chemistry. Heavy structure (~60+
  lbs). Note: Legacy status. Exhibiting active capacity degradation, severe
  weight penalty, lack of internal state telemetry readout.

#### Smart Shore Charger / Maintainer

* **Date Bought:** 2020-11-30
* **Price Spent:** $65.00 USD
* **Title/Description:** NOCO GENIUS10: 10A 6V/12V Smart Battery Charger,
  Automatic Maintainer & Trickle Charger
* **Source URL:** https://www.amazon.com/dp/B07W3QT226
* **Detailed Specifications:** 10-Amp dynamic output charging capacity for
  6V and 12V systems. Supports Lead-Acid, AGM, and Lithium-Ion LiFePO4 profiles.
  Integrated automatic temperature compensation loops, desulfation algorithms,
  and overcharge tracking protection.

#### DC-to-AC Vehicle Power Inverter

* **Date Bought:** 2023-09-10
* **Price Spent:** $59.99 USD
* **Title/Description:** POTEK 750W Power Inverter 12V DC to 110V AC Car Adapter
* **Source URL:** https://www.amazon.com/dp/B01FEUD9OO
* **Detailed Specifications:** 750 Watts continuous power allocation (1500 Watts
  peak surge boundary). Translates 12V DC input to 110V AC output. 2x standard
  AC outlets, 2x USB charging ports (5V/2A). Built-in cooling fans and high/low
  voltage protection gates. Used exclusively to charge client laptop,
  communications gear, and drive a daily 30-second blender run.

#### Portable Solar Panel Array Kit (Alpha)

* **Date Bought:** 2021-06-30
* **Price Spent:** $220.00 USD
* **Title/Description:** Renogy 100W Portable Solar Panel Kit with 20A Charge
  Controller
* **Source URL:** https://www.amazon.com/dp/B079JVBVL3
* **Detailed Specifications:** 100W foldable Monocrystalline N-Type array
  layout. 25% cell efficiency metric. Tempered glass shell. Pre-wired with a 20A
  PWM charge controller. Telemetry state: Mechanical support legs broken, local
  digital status display fully functional.

#### Portable Solar Panel Array Kit (Beta)

* **Date Bought:** 2018-12-02
* **Price Spent:** $275.00 USD
* **Title/Description:** Renogy 100W Portable Solar Panel Kit with 20A Charge
  Controller
* **Source URL:** https://www.amazon.com/dp/B079JVBVL3
* **Detailed Specifications:** 100W foldable Monocrystalline N-Type array
  layout. 25% cell efficiency metric. Tempered glass shell. Pre-wired with a 20A
  PWM charge controller. Telemetry state: Mechanical support legs fully
  operational, local digital status display completely non-functional due to
  Burning Man rain flooding.

#### Legacy Decommissioned Power Station

* **Date Bought:** 2024-05-08
* **Price Spent:** $319.00 USD
* **Title/Description:** Jackery Explorer 500 v2 Portable Power Station
* **Source URL:** https://www.amazon.com/dp/B0FR555DVH
* **Detailed Specifications:** 512Wh LiFePO4 battery storage, 500W AC output
  engine. **STATUS: DECOMMISSIONED/NON-FUNCTIONAL.** Completely corroded and
  rendered inoperable due to Burning Man alkaline playa dust infiltration.

## Equipment Acquisition Pipeline

This section catalogs pending hardware evaluations required to stabilize global
operations across nomadic and static deployments.

### Tier 1/2 Basement Safety Upgrades
* **Target Equipment:** Uninterruptible Power Supply (UPS) for Location B.
* **Functional Mandate:** Must support pure sine wave AC output to safely
  protect the Binardat 10G backplane, GMKtec K8 Plus, and GMKtec EVO-X2 against
  grid voltage fluctuations or micro-blackouts in Lethbridge, AB. Must support
  an open network management interface (e.g., USB HID or SNMP via NUT/apcupsd)
  so that `sre_incident` can track grid drop events and cleanly command the
  OpenClaw database to run a safe `VACUUM` and graceful system shutdown before
  battery depletion.

### Van Electrical Power Infrastructure Expansion
* **Target Equipment:** Pure Sine Wave High-Output Inverter (1500W - 2000W).
* **Functional Mandate:** Required to scale van operations as mobile computing,
  tool usage, and logistics workloads grow. The current Potek 750W modified sine
  wave inverter is heavily constrained and insufficient for expanded
  multi-modality audio/video processing stations or heavy inductive tool draw.

### Nomadic Satellite Uplink Optimization
* **Target Equipment:** Next-Generation Flat/Starlink Mini Array Hardware.
* **Functional Mandate:** Under evaluation by the `sre_power` agents to reduce
  setup times, minimize power profiles, and remove the mechanical failure
  vectors of the legacy 2022 Actuated dish while tracking WAN performance across
  varying geographical terrains.

## Agent Hierarchy & Topologies

The system enforces a strict Vertical Command Structure to prevent routing loops
and context dilution. Agents do not communicate peer-to-peer across domains.

### The Global Routing Layer

- **`judge`** [simple-model]: Intent classifier. Protects token budgets via
  continuous thresholding into 4 tiers (`simple`, `medium`, `complex`,
  `frontier`).
- **`orchestrator_lead`** [medium-model]: Global DAG generator. Delegates
  exclusively to the Team Leads.
- **`generalist`** [complex-model]: Handles unmatched general-knowledge queries.

### The Software Team

The roles required to build, test, and deploy robust software are logically
delineated below. While these roles represent the necessary capabilities, they
do not mandate a 1:1 agent-to-role ratio.

| Role               | Core Skills Needed                                                | OpenClaw Permissions                                                 |
|--------------------+-------------------------------------------------------------------+----------------------------------------------------------------------|
| Architect          | System design, technical stack selection, interface definition.   | File read/write (workspace-limited).                                 |
| Lead Developer     | Code implementation, refactoring, library management.             | Shell execution, file write.                                         |
| QA / Tester        | Test case generation, test harness execution, edge-case analysis. | Shell execution (test runner only).                                  |
| UX / UI Designer   | Translate aesthetic goals into component structures (HTML/CSS)    | File read/write (UI components), Shell execution (local dev server). |
| DevOps / SRE       | Generates CI/CD pipelines, Dockerfiles, and deployment manifests. | Shell execution (Docker/Systemctl), File write (Manifests).          |
| Security Auditor   | API key sanitization, dependency vulnerability scanning.          | Network access (strictly monitored).                                 |
| Product Manager    | Requirement validation, final product sign-off.                   | Read-only access to transcripts.                                     |
| Telemetry Analyst  | Parsing JSONL logs, resource cost calculation.                    | System stats (CPU/RAM/Network hooks).                                |
| Documentation Spec | Technical writing, API documentation, README generation.          | File write.                                                          |
| Optimization Eng   | Profiling code, algorithmic efficiency improvements.              | Shell execution (profiling tools).                                   |
| Integration Lead   | Managing dependencies, ensuring build stability.                  | Package manager access (npm/pip).                                    |
| Final Validator    | Qualitative peer review, "sanity checking" logic.                 | Read-only; human-in-the-loop (optional).                             |

#### Organizational Density: The 3 vs 6 vs 12 Agent Debate

When configuring an autonomous team, the density of agents presents distinct
architectural trade-offs:

*   **3 Agents (High Density):** Grouping roles into just "Thinker", "Doer",
    and "Tester" minimizes the overhead of inter-agent message passing (reducing
    latency and token burn). However, it introduces severe *Semantic Bleed*. A
    single agent tasked with writing code, managing CI pipelines, and designing
    UI components will suffer from conflicting tool permissions (violating the
    principle of least privilege) and diluted context windows.

*   **12 Agents (One Per Role):** Creating a dedicated agent for every
    single role ensures pristine separation of concerns and absolute
    least-privilege security boundaries. However, this creates a massive, deep
    DAG graph. The latency delay caused by 12 sequential API hops, compounded by
    the token cost of passing the entire project context through `sessions_send`
    12 times, makes this unviable for real-time human interaction.

*   **6 Agents (The Current Synthesis):** A 6-agent topology strikes the
    optimal balance. It provides clear delineation between "Thinkers" (Lead,
    Orchestrator), "Doers" (Dev, QA), and "Monitors" (Auditor, PM), while
    mapping perfectly to hardware model tiers (e.g., complex reasoning models
    for thinkers, cheap/fast models for monitors).

#### Current Agent Mapping & Justification

Our current setup utilizes 6 specialized agents, mapping the 12 required roles
into synergistic clusters:

- **Lead:** `software_lead` [complex-model]
  - *Role Mappings:* Final Validator, Technical Consultant.
  - *Justification:* Acts purely as the human interface. Defers execution to the
    orchestrator, preventing the conversational agent from becoming bogged down
    in code syntax.

- **Worker:** `software_orchestrator` [complex-model]
  - *Role Mappings:* Architect, Documentation Spec.
  - *Justification:* Operates as a strict state machine. It writes the schemas
    and structural documentation, then creates the localized DAGs to delegate
    the raw coding labor downward.

- **Worker:** `software_dev` [medium-model]
  - *Role Mappings:* Lead Developer, UX/UI Designer, Optimization Eng, Integration Lead
  - *Justification:* The core implementer. It is granted the most dangerous
    tools (raw shell execution and package management). Grouping UI/UX and
    Optimization here prevents the need to pass massive code files back and
    forth between multiple specialized developers.

- **Worker:** `software_qa` [medium-model]
  - *Role Mappings:* QA / Tester.
  - *Justification:* Strictly segregated from `software_dev` to ensure tests are
    written against the Acceptance Criteria, not implicitly biased by how the
    developer wrote the implementation.

- **Worker:** `software_auditor` [simple-model]
  - *Role Mappings:* Security Auditor, Telemetry Analyst.
  - *Justification:* A lightweight, paranoid agent running on a fast model
    (`gemma4:e4b`). It scans files and parses logs continuously in the
    background via cron heartbeats without burning expensive API credits.

- **Worker:** `software_pm` [simple-model]
  - *Role Mappings:* Product Manager.
  - *Justification:* Another lightweight, asynchronous agent. It strictly
    validates final outputs against initial constraints and nags the human for
    unblocked sprint tickets via heartbeats.

- *(Note: The DevOps / SRE roles are deferred entirely to the dedicated `sre`
  team in the global cluster, isolating infrastructure modifications from
  application logic).*

### The Research Team

*Domain: OSINT, financial modeling, and ambient technology scanning.*

- **Lead:** `research_lead` [complex-model] - Research consultation and conversational strategy.
- **Worker:** `research_orchestrator` [complex-model] - Briefing compilation and local DAG delegation.
- **Worker:** `research_scout` [medium-model] - Large-context web scraping and HTML extraction.
- **Worker:** `research_quant` [medium-model] - Python-based math and multi-currency analysis.
- **Worker:** `research_scanner` [complex-model] - Academic paper and patent tracking.
- **Worker:** `research_concierge` [simple-model] - Physical-world routing, visa, and hardware sourcing.

### The Self (Modeling) Team

*Domain: Psychological sandbox, relational topologies, and biometric evaluation
(Eudaimonia/Hedonia/Health).*

- **Lead:** `self_lead` [complex-model] - Psychological consultation and conversational strategy.
- **Worker:** `self_orchestrator` [complex-model] - Models strict data pipelines and local DAG delegation.
- **Worker:** `self_council` [frontier-model] - Secular humanist mixture-of-experts synthesis.
- **Worker:** `self_simulator` [medium-model] - Ephemeral sandbox twin for testing interventions.
- **Worker:** `self_mirror` [complex-model] - Cognitive friction and logical fallacy detection.
- **Worker:** `self_sociologist` [medium-model] - Non-monogamous network graph topology analysis.
- **Worker:** `self_archivist` [simple-model] - Air-gapped biometric and digital exhaust retrieval.
- **Worker:** `self_integrator` [simple-model] - Routine translation and calendar blocking.

### The Media Team

*Domain: Creative asset generation and VRAM cold-swap execution.*

- **Lead:** `media_lead` [complex-model] - Media consultation and conversational strategy.
- **Worker:** `media_orchestrator` [complex-model] - Modality delegation and hardware concurrency limits.
- **Worker:** `media_image` [flux-1-dev] - SFW diagram and graphic layout rendering.
- **Worker:** `media_imagex` [pony-diffusion-v6-xl] - NSFW anatomical character styling.
- **Worker:** `media_video` [complex-model] - SFW temporal synthesis and motion vectors.
- **Worker:** `media_videox` [complex-model] - NSFW temporal synthesis via Image-to-Video.
- **Worker:** `media_audio` [complex-model] - SFW voice cloning and text-to-speech.
- **Worker:** `media_audiox` [complex-model] - NSFW sound effects and foley generation.
- **Worker:** `media_text` [complex-model] - SFW creative story writing and script generation.
- **Worker:** `media_textx` [frontier-model] - NSFW explicit creative writing and prose.

### The SRE (Grid) Team

*Domain: Cluster stability, distributed network resilience, and system administration.*

- **Lead:** `sre_lead` [complex-model] - SRE consultation and conversational strategy.
- **Worker:** `sre_orchestrator` [complex-model] - Disaster recovery, hardware stability, and local DAG delegation.
- **Worker:** `sre_incident` [complex-model] - Emergency graceful degradation protocols.
- **Worker:** `sre_power` [medium-model] - Remote monitoring of the Transit van's solar/battery telemetry.
- **Worker:** `sre_telemetry` [simple-model] - Log parsing and memory leak detection.
- **Worker:** `sre_network` [simple-model] - Tailscale ACLs and remote tunnel latency to the van.
- **Worker:** `sre_db` [simple-model] - PostgreSQL/pgvector vacuuming and index health.
- **Worker:** `sre_thermal` [simple-model] - Temperature throttling and hardware protection for the basement nodes.
- **Worker:** `sre_storage` [simple-model] - NVMe wear tracking and volume pruning.
- **Worker:** `sre_sysadmin` [medium-model] - Host-level shell commands and file manipulation.
- **Worker:** `sre_bandwidth` [simple-model] - Uplink management and Starlink latency profiling.

### The Health Team

*Domain: Physiological data orchestration, clinical diagnostics,
metabolic/vascular/endocrine protocols, and physical rehabilitation.*

- **Lead:** `health_lead` [complex-model] - Health consultation and conversational strategy.
- **Worker:** `health_orchestrator` [complex-model] - Diagnostic synthesis and local DAG delegation.
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

### The Finance Team

*Domain: Financial modeling, market analysis, intrinsic valuation, risk
assessment, tax strategy, and portfolio allocation.*

- **Lead:** `finance_lead` [complex-model] - Financial consultation and conversational strategy.
- **Worker:** `finance_orchestrator` [complex-model] - Financial orchestration and local DAG delegation.
- **Worker:** `finance_manager` [complex-model] - Portfolio allocation, position sizing, and Buy/Hold/Sell execution plans.
- **Worker:** `finance_risk` [complex-model] - Thesis counter-analysis, structural risk identification, and stress testing.
- **Worker:** `finance_crypto` [medium-model] - On-chain analysis, tokenomics, and smart contract auditing.
- **Worker:** `finance_data` [medium-model] - Raw financial data ingestion, SEC filings/PDF extraction, and scraping.
- **Worker:** `finance_fundamental` [medium-model] - DCF modeling, balance sheet analysis, and intrinsic valuation.
- **Worker:** `finance_quant` [medium-model] - Price action, momentum metrics, and technical indicators (RSI, MACD).
- **Worker:** `finance_tax` [simple-model] - Capital gains calculations, cross-border tax implications, and asset location.

### The Social Team

*Domain: Platform publishing, audience engagement, social SEO, and community management.*

- **Lead:** `social_lead` [complex-model] - Cross-platform consultation and conversational strategy.
- **Worker:** `social_orchestrator` [complex-model] - Cross-platform strategy and local DAG delegation.
- **Worker:** `social_youtube` [medium-model] - Video SEO, chapters, timestamps, and comment parsing.
- **Worker:** `social_reddit` [medium-model] - Subreddit engagement and organic tone matching.
- **Worker:** `social_bluesky` [simple-model] - Decentralized short-form publishing.
- **Worker:** `social_linkedin` [complex-model] - Professional networking and long-form B2B articles.
- **Worker:** `social_facebook` [medium-model] - Group administration and community posts.
- **Worker:** `social_twitter` [simple-model] - High-frequency hooks, threads, and short-form text.
- **Worker:** `social_instagram` [medium-model] - Visual descriptions, hashtag SEO, and carousel planning.
- **Worker:** `social_tiktok` [medium-model] - Short-form video hooks, trend analysis, and descriptions.
- **Worker:** `social_snapchat` [simple-model] - Ephemeral messaging and youth demographic framing.
- **Worker:** `social_pinterest` [medium-model] - Visual search SEO and board curation.
- **Worker:** `social_discord` [medium-model] - Real-time chat moderation, webhooks, and server rules.

## Structural Interdependencies (Maintenance Ledger)

As the OpenClaw environment evolves, failing to update paired files will result
in architectural breakdown, routing loops, or VRAM exhaustion. Adhere to the
following cascade rules:

### Adding or Removing a Subordinate Agent

If you add a new worker (e.g., `sre_security`) to an existing team:

1. **Update the Team Lead's System Prompt:** Modify
   `workspace/agents/<team>/<lead>/SOUL.md`. You must explicitly add the new
   agent to the `LOCAL DELEGATION MATRIX` section. The Team Lead cannot route to
   agents it does not know exist.

2. **Update YAML & LiteLLM:** Ensure the `model:` specified in the new agent's
   YAML utilizes a conceptual tier (`simple-model`, etc.) registered in the
   Gateway proxy.

### Adding a New Team (Domain)

If you create a completely new team branch:

1. **Update the Global Orchestrator:** Modify
   `workspace/agents/orchestrator/SOUL.md`. You must append the new Team Lead to
   the `HIERARCHICAL DELEGATION MATRIX`.

2. **Update the Escalation Protocol:** You must update the `THE ESCALATION
   PROTOCOL` section inside the `SOUL.md` of **every existing Team Lead** so
   they know they can escalate tasks requiring the new team's specific
   capabilities.

### Upgrading Hardware (Changing VRAM/RAM capacity)

If you add a new host or upgrade memory constraints:

1. **Update Telemetry Memory:** Modify
   `workspace/agents/sre/telemetry/MEMORY.md` so the Warden agent knows the new
   absolute limits before throwing an Out-Of-Memory alert.

2. **Update Producer Memory:** Modify
   `workspace/agents/media/orchestrator/MEMORY.md`. If you gain enough VRAM to
   keep Flux and Qwen hot simultaneously, you must remove the strict
   concurrency/cold-swap limits from the Orchestrator's configuration.

## Tier Journey & Hardware Scaling Projections

The architectural path maps out the progressive integration of heavy compute and
the eventual repositioning of edge nodes as the data demands increase.

- **Tier 0:** MacBook Air has been tested as the isolated baseline.
- **Tier 1:** GMKtec K8 Plus has been partially tested (still under active stabilization).
- **Tier 2:** GMKtec K8 Plus (Control Plane) + GMKtec EVO-X2 (Compute Plane) is fully active and operational. The compute plane successfully handles bare-metal Ollama inference.
- **Tier 2+:** Planning on purchasing 1-3 Mac Studio M5 Ultras in October 2026 when they are released, to exponentially expand the 'compute' farm capabilities.
- **Tier 3-5:** When the Mac Studio(s) are active, the GMKtec EVO-X2 will be repurposed strictly to the 'execution' plane. A new, specialized workstation (see `docs/PLANES.md`) will be sourced for the 'archive' plane.

### Hardware-to-Model Mappings

Based on VRAM limits, optimal model loading targets for current and future node
acquisitions are detailed below:

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

### Media-To-Model Mappings (SFW vs NSFW)

Media generation workloads must be strictly bifurcated based on the model's
safety alignment and censorship mechanisms.

**Video Generation**

*   **SFW Models:** `LTX-2.3` (Optimized DiT, 4K at 50fps), `Wan 2.7` (MoE
    Diffusion), `CogVideoX`.

*   **NSFW Models:** `Wan 2.7 (TI2V-5B Variant)` (Used for I2V animation of NSFW
    base images), `Mochi 1` (Permissive open-weights), `LTX-2.3 (IC-LoRA
    Workflows)`.

**Image Generation**

*   **SFW Models:** `flux-1-dev` (Highly detailed, strict licensing/alignment),
    `Stable Diffusion 3 Large`.

*   **NSFW Models:** `pony-diffusion-v6-xl` (Uncensored anatomical styling).

**Audio Generation**

*   **Speech (SFW/NSFW Agnostic):** `XTTSv2`, `Parler-TTS`. (TTS models lack
    RLHF filters and will read any provided script).

*   **Foley/Sound Effects:** Custom fine-tunes of `AudioLDM2` required for
    specific non-speech generations (e.g., moans, environmental sounds).

**Text Generation (Erotica)**

*   **SFW General Models:** `qwen-3-32b`, `llama-4-109b`. (Heavily RLHF-aligned;
    will refuse or sanitize explicit prompts).

*   **NSFW Erotica Models:** `Midnight-Miqu-70B`,
    `Llama-3-70B-Instruct-uncensored` (Stripped of corporate alignment filters
    for creative writing).
