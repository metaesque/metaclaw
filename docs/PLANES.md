# MetaClaw Hardware Planes

The MetaClaw architecture isolates infrastructure into functional planes based on their resource utilization profiles and security trust levels.

## The Control Plane {#control}

* **Aka**: The Ingress & Routing Hub
* **Profile**: High network I/O, low CPU, low RAM.
* **Justification**: This is the high-speed nervous system. It dictates traffic
  flow and maintains ephemeral state, operating flawlessly on low-power devices.
* **Services**: proxy-reverse, iam, proxy, gateway, secret, event, cache, queue

### Hardware Recommendations for The Control Plane

#### GMKtec Gaming Mini PC K8 Plus
* **Price**: ~$399.99 - $519.00
* **Specs**: AMD Ryzen 7 8845HS, 32GB DDR5, 1TB SSD, Dual 2.5GbE
* **URL**: [Link](https://www.gmktec.com/products/amd-ryzen-7-8845hs-mini-pc-nucbox-k8)
* **Strengths**: Excellent network bridging with dual 2.5GbE; incredible price-
  to-performance ratio for a gateway node.
* **Weaknesses**: The 32GB RAM ceiling is extremely tight if attempting to run
  memory-heavy background tasks on the same node.

#### Minisforum MS-01
* **Price**: ~$649.00 (Barebones Base) - $869.00
* **Specs**: Intel Core i9-13900H, up to 64GB RAM, Dual 10GbE SFP+, Dual 2.5GbE
* **URL**: [Link](https://www.newegg.com/minisforum-barebone-systems-mini-pc-intel-core-i9-13900h/p/2SW-002G-000K7)
* **Strengths**: Unmatched homelab networking with dual 10GbE and 2.5GbE ports;
  provides massive routing throughput across the Tailscale mesh.
* **Weaknesses**: Intel H-series chips can run hot in tiny chassis, potentially
  leading to thermal throttling under sustained load.

#### Protectli Vault VP4670
* **Price**: ~$600.00 - $800.00 (Configuration dependent)
* **Specs**: Intel Core i7, 6x 2.5GbE Ports, Fanless Design
* **URL**: [Link](https://protectli.com/vault-6-port/)
* **Strengths**: Engineered specifically for 24/7 routing and firewall proxying;
  fanless design ensures zero dust intake and absolute acoustic silence.
* **Weaknesses**: Older generation CPU provides lower raw compute for non-
  routing tasks; RAM capacity is generally more limited.

#### Supermicro SYS-E300-9D
* **Price**: ~$1,066.00 (Barebones)
* **Specs**: Intel Xeon D-2123IT, ECC Memory Support, Quad 1GbE, Dual 10GbE, IPMI
* **URL**: [Link](https://www.walmart.com/ip/SUPERMICRO-SYS-E300-9D-4CN8TP-Compact-Server-Barebone/290133537)
* **Strengths**: Enterprise-grade edge server with IPMI for remote out-of-band
  management; ECC memory absolutely prevents routing table corruption.
* **Weaknesses**: Significantly more expensive than consumer equivalents; active
  cooling fans can be excessively loud in a home environment.

## The Compute Plane {#compute}

* **Aka**: The Intelligence Engine
* **Profile**: Extreme GPU VRAM, maximum memory bandwidth, high power draw.
* **Justification**: LLM inference requires dedicated PCIe acceleration. It must
  be isolated to prevent VRAM starvation from impacting other critical services.
* **Services**: runner

### Hardware Recommendations for The Compute Plane

#### Apple Mac Studio M5 Ultra
* **Price**: ~$3,999.00+ (Projected)
* **Specs**: Projected up to 36-core CPU, 80-core GPU, ~1.2 TB/s Memory Bandwidth, 128GB+ Unified Memory.
* **URL**: [Link](https://www.apple.com/mac-studio/)
* **Strengths**: Unparalleled unified memory bandwidth (~1.2 TB/s) bypasses PCIe
  bottlenecks, enabling massive RAG payload evaluation faster than multi-GPU
  rigs.
* **Weaknesses**: Entirely locked ecosystem; no possibility of internal hardware
  expansion or VRAM upgrades after purchase.

#### Custom Multi-GPU Workstation
* **Price**: ~$10,000.00 - $15,000.00+
* **Specs**: AMD Threadripper PRO, 4x NVIDIA RTX 4090 (96GB total VRAM), 256GB ECC RAM
* **URL**: [Link](https://www.pugetsystems.com/workstations/)
* **Strengths**: Achieves substantially higher tokens-per-second generation
  speeds than Apple Silicon via Tensor Parallelism across dedicated GDDR6X
  memory.
* **Weaknesses**: Extremely high power draw, massive physical footprint, and
  complex cooling requirements.

#### Apple Mac Pro (M-Series Ultra)
* **Price**: ~$6,999.00+
* **Specs**: M2/M3 Ultra (up to 192GB Unified Memory), 800 GB/s bandwidth, PCIe expansion slots.
* **URL**: [Link](https://www.apple.com/mac-pro/)
* **Strengths**: Uses the exact same silicon as the Mac Studio but placed in a
  massive thermal enclosure to completely prevent thermal throttling.
* **Weaknesses**: Severe Apple Tax for the enclosure; internal PCIe slots cannot
  be used to add discrete NVIDIA GPUs for inference.

#### Lambda Tensorbook
* **Price**: ~$3,007.49 - $3,499.00
* **Specs**: Intel Core i7, NVIDIA RTX 3080/4080 (16GB), 64GB RAM, 1TB NVMe
* **URL**: [Link](https://lambdalabs.com/deep-learning/laptops/tensorbook)
* **Strengths**: A portable, validated, Linux-native stack specifically tuned
  out-of-the-box for PyTorch and local LLM inference.
* **Weaknesses**: Laptop form factor restricts maximum VRAM (16GB limit),
  forcing reliance on smaller 8B/14B models or heavy quantization.

## The Archive Plane {#archive}

* **Aka**: Context & Telemetry
* **Profile**: Massive RAM capacity, extreme disk IOPS (NVMe), heavy storage.
* **Justification**: This plane manages all 'Trusted Data'. Vector databases
  ingest massive streams of data and require enormous RAM. Keeping these safe
  from untrusted execution workloads is a strict SRE requirement.
* **Services**: memory, vcs, logger, tracer

### Hardware Recommendations for The Archive Plane

#### GMKtec EVO-X2
* **Price**: ~$1,999.99 (Base) - $2,666.99 (128GB/2TB spec)
* **Specs**: AMD Ryzen AI Max+ 395, 128GB LPDDR5X, 2TB PCIe 4.0 SSD
* **URL**: [Link](https://www.gmktec.com/products/gmktec-evo-x2-ai-mini-pc-amd-ryzen%E2%84%A2-ai-max-395-1)
* **Strengths**: 128GB RAM provides a massive `shared_buffers` cache, allowing
  PostgreSQL to keep entire vector indexes in memory for sub-millisecond
  semantic recall.
* **Weaknesses**: Lacks ECC memory, making it vulnerable to silent bit-flips
  corrupting the HNSW index graph over long uptimes.

#### System76 Thelio Major
* **Price**: ~$3,800.00 (Used) - $6,661.00+ (New)
* **Specs**: AMD Threadripper PRO, up to 512GB ECC DDR5, multiple U.2/NVMe slots
* **URL**: [Link](https://system76.com/desktops/thelio-major)
* **Strengths**: ECC memory support prevents database corruption; massive
  internal bays allow creating striped RAID arrays for high-speed telemetry
  logs.
* **Weaknesses**: High upfront cost and large physical footprint compared to
  mini-PCs.

#### Dell Precision 7960 Tower
* **Price**: ~$9,999.00+
* **Specs**: Intel Xeon W-3400/3500 series, up to 4TB ECC RAM, front-accessible NVMe flex-bays
* **URL**: [Link](https://www.dell.com/en-hk/shop/pcs-desktop-computers/precision-7960-tower/spd/precision-t7960-workstation)
* **Strengths**: Enterprise workhorse with hot-swappable drives, allowing you to
  easily scale your Context Lake into the hundreds of terabytes seamlessly.
* **Weaknesses**: Extremely expensive enterprise markup; proprietary
  motherboard/PSU form factors limit future DIY upgrades.

#### Custom Asrock Rack EPYC 8004 'Siena' Server
* **Price**: ~$1,046.00 (Barebones Motherboard/CPU Combo)
* **Specs**: AMD EPYC 8004/4004 series, 96 PCIe Gen 5 lanes
* **URL**: [Link](https://www.newegg.com/)
* **Strengths**: 96 PCIe Gen 5 lanes allow attaching dozens of NVMe drives
  directly to the CPU without chipset bottlenecks, achieving unparalleled log
  ingestion speeds.
* **Weaknesses**: Requires custom DIY server assembly and specialized cooling
  solutions.

## The Execution Plane {#execution}

* **Aka**: The Blast Zone
* **Profile**: Heavy multi-core CPU, highly dynamic and unpredictable RAM usage.
* **Justification**: This plane executes volatile, untrusted code. It is an
  operational hazard physically isolated to ensure that a rogue task cannot
  crash the Control Plane or corrupt the Data Plane.
* **Services**: browser, fetcher, searcher, sandbox, ci

### Hardware Recommendations for The Execution Plane

#### GMKtec EVO-X2
* **Price**: ~$1,999.99 (Base) - $2,666.99 (128GB/2TB spec)
* **Specs**: AMD Ryzen AI Max+ 395 (16C), 128GB LPDDR5X, 2TB PCIe 4.0 SSD
* **URL**: [Link](https://www.gmktec.com/products/gmktec-evo-x2-ai-mini-pc-amd-ryzen%E2%84%A2-ai-max-395-1)
* **Strengths**: 16 cores and 128GB RAM securely isolate dozens of concurrent
  `gVisor` sandboxes without starving the host OS.
* **Weaknesses**: Mobile processor cooling constraints may cause it to
  temporarily throttle under massive, sustained CI/CD parallel compilation
  workloads.

#### Lenovo ThinkStation P360 Ultra
* **Price**: ~$639.00 - $1,826.00
* **Specs**: Intel Core i5/i9 (desktop class), up to 128GB ECC RAM, 4-liter chassis
* **URL**: [Link](https://www.lenovo.com/us/outletus/en/p/workstations/thinkstation-p-series/thinkstation-p360-ultra-intel/30g1000lus)
* **Strengths**: Fits a full desktop-class 125W CPU into a tiny 4-liter chassis,
  offering significantly higher single-core turbo frequencies to accelerate
  Python code compilation and Docker image builds.
* **Weaknesses**: Custom form factor makes part replacement difficult; active
  cooling can get extremely loud under load.

#### Minisforum BD790i
* **Price**: ~$599.00 (Motherboard/CPU Combo)
* **Specs**: AMD Ryzen 9 7945HX3D (16C/32T with 3D V-Cache), Mini-ITX
* **URL**: [Link](https://www.ebay.com/itm/257253513621)
* **Strengths**: Massive 3D V-Cache and blistering fast burst performance for
  rapidly spawning and destroying dozens of concurrent, ephemeral `gVisor`
  sandboxes.
* **Weaknesses**: It is only a motherboard/CPU combo, requiring the user to
  build a custom ITX chassis, source RAM, storage, and a power supply.

#### System76 Thelio Mega
* **Price**: ~$5,999.00+
* **Specs**: AMD Ryzen Threadripper 7000 (up to 64+ cores), up to 256GB ECC RAM
* **URL**: [Link](https://system76.com/desktops/thelio-mega)
* **Strengths**: Provides the raw 64+ hardware cores required to prevent thread
  contention when running massive parallel swarms (e.g., 50 agents scraping
  concurrently) natively under Linux.
* **Weaknesses**: Massive cost and power draw for sandboxing workloads, usually
  overkill unless the agent swarm is operating at an enterprise scale.
