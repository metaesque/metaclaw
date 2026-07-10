# OpenClaw Framework: Service Expansion Roadmap

*Note: With the upgrade to OpenClaw 2026.6.8, Meta<Claw> has formally adopted an "un-opinionated" design goal. We aim to make it incredibly easy for non-technical users to get OpenClaw running, without placing them in a straight-jacket once the environment is operational. All future roadmap items are evaluated against this ethos.*

This document outlines the prioritized architectural strategy for integrating future software capabilities and migrating across hardware tiers.

---

## 📋 PRIORITY ACTION BACKLOG (July 2026)

The following tasks are prioritized for immediate execution to stabilize the Tier 1/Tier 2 architecture and resolve current configuration friction.

1. **Abstract Conceptual Models (YAML Sweep):** *STATUS: MOSTLY COMPLETE.* All core models have been migrated to generic tiers (`simple-model`, `complex-model`, etc.). *Pending:* The `media` team still utilizes hardcoded models (`pony-diffusion-v6-xl`, `flux-1-dev`, `local-video-diffusion`, `local-audio-pipeline`). We must establish an abstracted 'SFW vs NSFW' tiering system for multimodal video and image generations.
2. **Implement Multi-Model Comparison Framework:** Design an internal testing harness allowing a single agent profile to seamlessly invoke and evaluate output across multiple distinct models (e.g., comparing LTX-2.3 vs Wan 2.7 for SFW video generation) on the same prompt structure to determine long-term viability.
3. **Tier 1 vs. Tier 2 LiteLLM Configuration:** Define the mapping logic in `services/proxies/litellm/config.yaml`. For Tier 1 (K8 Plus only, 32GB RAM), `medium-model` and `complex-model` must route to cloud APIs. For Tier 2 (EVO-X2 active), they must seamlessly route over Tailscale to the local inference node.
4. **OpenClaw Native Development Handoff:** Validate the "Middle Reasoning" HTN by prompting the local Orchestrator to execute a multi-step codebase refactor. Monitor the logs to verify the `sessions_send` tool is executing properly, proving the agent swarm can now take over framework development.
5. **Refactor `patch_routing.py` (The CLI Refactor):** Rewrite the script so that it configures OpenClaw using official CLI commands (`openclaw config set`, `openclaw agents add`) rather than brittle, direct manipulation of `openclaw.json`.
6. **Build PostgreSQL Session Sync (ETL):** Replace the cumbersome `config` directory archiving process. Write a lightweight Python daemon/cron job to tail OpenClaw's `sessions.jsonl` files, parse the dictionaries, and `INSERT` the prompt/response pairs directly into a structured PostgreSQL schema, actively preserving the agent's stream of consciousness in a robust database.
7. **Implement a `vcs` Provider:** Integrate a Local Version Control System (e.g., Gitea/Forgejo) to act as a secure, local scratchpad for agents to iteratively push and test code modifications before submitting final PRs to the main GitHub repository.
8. **Implement a `ci` Provider:** Integrate a Continuous Integration pipeline (e.g., Woodpecker/Drone) triggered by the local `vcs` to mathematically test agent-generated code inside the Execution sandbox.
9. **Automated CLI Output Redaction Script:** Write a Python utility to pipe and filter standard output from `make` and `docker` commands. The script should strip redundant lines and token-heavy delimiters (e.g., 80-character `===` blocks) to optimize pasted context windows for LLM interaction.
10. **Enhance `parse_prompts_oc.py`:** Add `--start` and `--end` flags for time-bounded queries, and an `--llm` flag to strip unneeded whitespace and human-readable formatting, delivering hyper-dense context directly to LLM agents.
11. **Profile-Driven Conceptual Model Mapping:** Update `bin/sysprofile.py` to interrogate the user (or automatically profile VRAM) to define the actual physical model strings (e.g., `ingu627/llama4-scout-q4:109b`) mapped to conceptual tiers. Store this in `profile.json` so `orchestrate.py` can automatically inject it into the proxy layer.

---

## 🟢 MILESTONE 1: The Tier 0 Foundation (Achieved)

**Status: COMPLETED (`stable-v1`)**
**Public Repository:** [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw)

**The Accomplishment:** We have successfully built and verified a working Tier 0 environment. MetaClaw now reliably bootstraps OpenClaw alongside its essential caching and observability services. We have transitioned framework development natively into the local OpenClaw agent workflow, granting it read/write workspace access to iteratively improve the ecosystem.

---

## 🟡 MILESTONE 2: The Tier 1 & Tier 2 Linux Migration

**Urgency: HIGH**
**Status: IN PROGRESS**

**Current Hardware State:**
The dedicated edge hardware has been successfully physically provisioned. Both nodes are running headless Ubuntu Server, are accessible remotely via Tailscale, can be managed seamlessly via Emacs TRAMP, and have the repository cloned into the `metaclaw` user's `$HOME` directory.
* **The Control Node:** GMKtec K8 Plus
* **The Compute Node:** GMKtec EVO X2

### Step A: Evolve the Control Node (Tier 1 Control Plane)
**Status: Mostly Complete.** The node successfully boots, handles remote Tailscale HTTPS UI access, and manages the 4-Tier Predictive Router.
1. **Ubuntu Optimization:** Refactored Makefiles and deployment scripts to account for headless Ubuntu constraints (e.g., bare-metal Tailscale lifelines, WebCrypto HTTPS requirements).
2. **Provider Diversification:** Expanded the `services` architecture to support robust, bare-metal or heavy-docker providers (PostgreSQL pgvector, VictoriaLogs, LiteLLM).
3. **Workspace Decoupling:** Safely extracted the agent definitions into the `mcwksp` repository to protect the mutable markdown brains during infrastructure resets.

### Step B: Evolve the Compute Node (Tier 2 Compute Plane)
**Status: COMPLETED.** The EVO X2 is actively running Ollama and Tailscale on bare-metal.
We have successfully configured the EVO X2 to act as the dedicated **Tier 2 LLM Runner** to eliminate expensive API costs for agent actions.
1. **Local Model Hosting:** (Completed) The LLM Runner (Ollama) is utilizing the EVO X2's Strix Halo APU and unified memory for high-speed local inference.
2. **Proxy Routing Matrix:** Update LiteLLM's `config.yaml` on the Control Node to route `medium-model` tasks (e.g., tool execution) to fast models on the K8 Plus, while routing `complex-model` tasks to massive reasoning models (e.g., Llama 4 109B) over the LAN to the EVO-X2.
3. **Hot/Cold Swapping:** Establish logic/timeout protocols within the runners to seamlessly swap specialized models (vision, video) into VRAM when required and evict them when idle.

---

## 🟢 MILESTONE 3: The Modular Routing & Un-opinionated Customization Refactor

**Urgency: HIGH**
**Status: COMPLETED**

As MetaClaw transitioned from an opinionated script into a general-purpose facilitator, we decoupled the rigid `openclaw.json` overwrites in favor of dynamic user customization.

**The Accomplishments:**
1. **The Sibling Directory Architecture:** We formally decoupled the user's data from the MetaClaw repository. The workspace now lives in `../workspace` and the databases in `../external`, completely isolating the user from destructive `git clean` operations.
2. **Interactive Bootstrapping:** `bin/customize.py` now allows users to cleanly select their preferred Prompt Routing Strategy and automatically hydrates an empty workspace from a `.workspace.template` if requested.
3. **Native Workspace Routing Plugins:** We abandoned the brittle JSON injection method for Prompt Routing. Instead of hacking `openclaw.json`, MetaClaw now compiles Lexical/Predictive JS logic into an official `openclaw.plugin.json` package directly inside the user's workspace (`.openclaw/extensions/metaclaw-routing`). OpenClaw natively discovers and loads this plugin during boot, allowing the system to use a local LLM Judge to intercept prompts and deflect them away from expensive Gemini API calls seamlessly.

---

## 🟡 MILESTONE 4: The CLI-First Configuration Refactor

**Urgency: MEDIUM**
**Status: PLANNED**

**Purpose:** To firmly establish MetaClaw as a facilitator rather than a dictator, we must migrate away from direct programmatic modification of `openclaw.json`. Hacking JSON keys directly is brittle across point-releases, risks corrupting the configuration (causing crash loops), and obscures the native mechanisms from the end-user. Instead, we will configure the Gateway using official OpenClaw CLI commands (e.g., `openclaw config set`, `openclaw agents add`). This strategy is more resilient, future-proof, and models best practices for users wanting to add agents themselves.

**The Role of YAML files in the Refactor:**
OpenClaw natively reads Markdown files (`SOUL.md`, `AGENTS.md`) for system prompts, but it does NOT natively read YAML files or frontmatter for configuration metadata. Therefore, we will retain the custom agent `.yaml` files in the workspace purely as Infrastructure-as-Code manifests. A Python bootstrapping script will parse these `.yaml` files to extract the `model`, `tools`, and `workspace` metadata, and then execute the corresponding `openclaw agents add` CLI commands in bulk to dynamically populate the gateway configuration on a fresh installation.

**Target Files for Cleanup:**
* `services/gateways/openclaw/patch_routing.py` (Must be refactored to utilize `subprocess.run` wrapping `openclaw config set` rather than direct JSON object manipulation).

---

## Phase 1: Safe Execution (Sandboxing)

* **Category:** `services/sandboxes/`
* **Target Providers:** `gVisor` (Local Linux hardening), `E2B` (Cloud ephemeral execution).
* **Purpose:** Move beyond the basic `docker-dood` implementation to prevent malicious or hallucinated agent code from escaping the container namespaces and corrupting the host OS.

## Phase 2: External Interaction (Browsers, Fetchers, and Searchers)

* **Categories:** `services/browsers/`, `services/fetchers/`, `services/searchers/`
* **Purpose:** Expand the Tier 0 demonstration capabilities into robust 24/7 background tasks. Implement visual DOM interpretation (`Skyvern`), action-caching to save API costs (`Stagehand`), and self-healing data extraction that doesn't break when CSS classes change.

## Phase 3: Source Truth & Reliability (VCS & CI)

* **Category:** `services/vcses/` & `services/ci/`
* **Target Providers:** `Forgejo / Gitea`, `Woodpecker CI / Drone`
* **Purpose:** As agents autonomously modify workspace files, we need absolute attribution. CI pipelines will mathematically prove the agent's code works against a test suite before it is deployed.

## Phase 4: Decoupling & Debugging (Queues & Tracing)

* **Category:** `services/queues/` & `services/tracers/`
* **Target Providers:** `RabbitMQ`, `OpenTelemetry + Jaeger / SigNoz`
* **Purpose:** Prevent timeouts during complex multi-agent swarms by decoupling synchronous HTTP calls. Provide deep visibility into latency spans to debug slow agent reasoning loops.

## Phase 5: Secure Public Ingress (Reverse Proxy & IAM)

* **Categories:** `services/proxies-reverse/`, `services/iam/`
* **Target Providers:** `Traefik / Caddy`, `Authelia / Authentik`
* **Purpose:** Expose specific agent endpoints (like a shared public webhook receiver) to external users via strict Multi-Factor Authentication and SSL termination.
