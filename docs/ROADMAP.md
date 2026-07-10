# OpenClaw Framework: Service Expansion Roadmap

*Note: With the upgrade to OpenClaw 2026.6.8, Meta<Claw> has formally adopted an "un-opinionated" design goal. We aim to make it incredibly easy for non-technical users to get OpenClaw running, without placing them in a straight-jacket once the environment is operational. All future roadmap items are evaluated against this ethos.*

This document outlines the prioritized architectural strategy for integrating future software capabilities and migrating across hardware tiers.

---

## 📋 PRIORITY ACTION BACKLOG (July 2026)

The following tasks are prioritized for immediate execution to stabilize the Tier 1/Tier 2 architecture and resolve current configuration friction.

1. **Refactor `patch_routing.py` (The CLI Refactor):** *CRITICAL TOP PRIORITY.* Rewrite the script so that it configures OpenClaw using official CLI commands (`openclaw config set`, `openclaw agents add`) rather than brittle, direct manipulation of `openclaw.json`. The new Python script must inject detailed comments and documentation into the generated OpenClaw Bash execution scripts, explaining the security ramifications and context of each CLI command (e.g., documenting the risks of `tools.agentToAgent.enabled`).
2. **Generalize Agent Domains:** Review and rewrite the domains and mandates of all teams and agents (e.g., `sre_lead`) so they are less MetaClaw-specific and broad enough to capture generic sysadmin, coding, and networking tasks reliably.
3. **Automated CLI Output Redaction Script:** Write a Python utility to pipe and filter standard output from `make` and `docker` commands. The script should strip redundant lines and token-heavy delimiters (e.g., 80-character `===` blocks) to optimize pasted context windows for LLM interaction within OpenClaw.
4. **Enhance `parse_prompts_oc.py`:** Add `--start` and `--end` flags for time-bounded queries, and an `--llm` flag to strip unneeded whitespace and human-readable formatting, delivering hyper-dense context directly to LLM agents.
5. **Decouple "Runner" from "Compute Plane":** Update the architecture so that a Control node running a small utility model (like the Judge) is not classified as a "Compute Plane." The Compute Plane should strictly define heavy inference nodes.
6. **Centralize Cluster Setup:** Modify `make setup` and `bin/sysprofile.py` to be an interactive, step-by-step prompt executed on the Master node that defines all nodes in the cluster and outputs a global `cluster.yaml` (or master `profile.json`), preventing split-brain network topologies.
7. **Profile-Driven Conceptual Model Mapping:** Update `bin/sysprofile.py` to interrogate the user to define the actual physical model strings (e.g., `ingu627/llama4-scout-q4:109b`) mapped to conceptual tiers, storing this in `profile.json` for dynamic proxy injection.
8. **Abstract Conceptual Models (YAML Sweep):** Establish an abstracted 'SFW vs NSFW' tiering system for multimodal video and image generations within the `media` team.
9. **Implement Multi-Model Comparison Framework:** Design an internal testing harness allowing a single agent profile to seamlessly invoke and evaluate output across multiple distinct models (e.g., comparing LTX-2.3 vs Wan 2.7) on the same prompt structure.
10. **Build PostgreSQL Session Sync (ETL):** Replace the cumbersome `config` directory archiving process with a lightweight Python daemon/cron job to tail OpenClaw's `sessions.jsonl` files and `INSERT` the prompt/response pairs directly into a structured PostgreSQL schema.

---

## 🟢 MILESTONE 1: The Tier 0 Foundation (Achieved)

**Status: COMPLETED (`stable-v1`)**
**Public Repository:** [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw)

**The Accomplishment:** We have successfully built and verified a working Tier 0 environment. MetaClaw now reliably bootstraps OpenClaw alongside its essential caching and observability services. We have transitioned framework development natively into the local OpenClaw agent workflow.

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

### Step B: Evolve the Compute Node (Tier 2 Compute Plane)
**Status: COMPLETED.** The EVO X2 is actively running Ollama and Tailscale on bare-metal.

---

## 🟢 MILESTONE 3: The Modular Routing & Un-opinionated Customization Refactor

**Urgency: HIGH**
**Status: COMPLETED**

As MetaClaw transitioned from an opinionated script into a general-purpose facilitator, we decoupled the rigid `openclaw.json` overwrites in favor of dynamic user customization, integrating Native Workspace Routing Plugins to intercept requests securely.

---

## Phase 1: Safe Execution (Sandboxing)
* **Category:** `services/sandboxes/`
* **Purpose:** Move beyond the basic `docker-dood` implementation to prevent malicious or hallucinated agent code from escaping the container namespaces and corrupting the host OS.

## Phase 2: External Interaction (Browsers, Fetchers, and Searchers)
* **Categories:** `services/browsers/`, `services/fetchers/`, `services/searchers/`
* **Purpose:** Expand the Tier 0 demonstration capabilities into robust 24/7 background tasks.

## Phase 3: Source Truth & Reliability (VCS & CI)
* **Category:** `services/vcses/` & `services/ci/`
* **Purpose:** As agents autonomously modify workspace files, we need absolute attribution and mathematical testing.

## Phase 4: Decoupling & Debugging (Queues & Tracing)
* **Category:** `services/queues/` & `services/tracers/`
* **Purpose:** Prevent timeouts during complex multi-agent swarms by decoupling synchronous HTTP calls.
