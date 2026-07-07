# MetaClaw Changelog

This document records significant changes and updates made to the MetaClaw framework.

## 2026-07-07
* **Workspace GitOps Decoupling:** Successfully isolated the user `workspace` directory into an independent, private repository (`mcwksp`) using `git-filter-repo`. Removed all workspace tracking from the MetaClaw monorepo to ensure destructive infrastructure resets never risk lobotomizing the agents' mutable `.md` brains.
* **4-Tier Predictive Routing:** Upgraded the `lexical_predictive.js` hook to support a 4-tier mechanical complexity scale (`simple`, `medium`, `complex`, `frontier`). Added a bypass mechanism leveraging an `is_lead: true` YAML flag to ensure the Judge does not override specialty models (like `flux-1-dev`) on leaf-node workers.
* **Middle Reasoning Topology:** Refactored agent architecture to strictly enforce a Hierarchical Task Network (HTN). Removed execution tools (`read_file`, `search_web`) from Team Leads, forcing them to use `frontier/complex` models exclusively for DAG generation and downward delegation (`sessions_send`), drastically reducing API token burn on trivial tool calls.
* **Unmatched Prompt Resolution:** Deployed a `generalist` agent and an `sre_sysadmin` agent. The Orchestrator's `SOUL.md` was updated with an "Unmatched Prompts" directive, preventing routing failures when a user's prompt falls outside the strict domain matrix.
* **Documentation Restructuring:** Split the monolithic `SERVICES.md` into `PLANES.md`, `TIERS.md`, and `SERVICES.md` to protect OpenClaw's context window during `read_file` operations. Updated `OC.md` to act as a lazy-loading index.

## 2026-07-04
* **Configuration State Archiving:** Overhauled the `clean-local-state` Makefile target. Instead of destructively deleting the OpenClaw `config` directory (which contains irreplaceable `.jsonl` session data), it now safely copies the entire directory to a timestamped archive within the external drive (`metaclaw-archive/config-<TIMESTAMP>`) before wiping the active deployment.
* **YAML and Markdown Decoupling:** Reverted a flawed design pattern that attempted to use Python to compile Markdown files from YAML frontmatter. OpenClaw agents possess the autonomy to modify their own Markdown files (`SOUL.md`, `AGENTS.md`) to learn over time. Overwriting them via an infrastructure script destroys this emerging consciousness. Going forward, `.yaml` files strictly manage infrastructure metadata (`model`, `tools`), while `.md` files natively act as the mutable brain.

## 2026-07-02
* **Native Workspace Routing Plugins**: Abandoned the legacy method of injecting JavaScript routing hooks via `openclaw.json` modification. This caused severe Zod validation death loops and Unix file permission conflicts. MetaClaw now compiles Prompt-to-Model routing logic (Lexical/Predictive) into an official Native OpenClaw Plugin package stored securely inside the user's workspace (`.openclaw/extensions/metaclaw-routing`).
* **Interactive Bootstrapping (`bin/customize.py`)**: Migrated prompt-routing strategy selection and workspace directory generation out of the `.env` templating engine and into a dedicated Python CLI wizard, drastically improving UX for non-technical users.
* **OpenClaw `BOOTSTRAP.md` Suppression**: Discovered that OpenClaw's onboarding ritual is triggered by cryptographic hashes of the default `.workspace.template/*.md` files. We successfully suppressed this unwanted behavior natively by injecting hidden HTML comments into the template files, breaking the hash match without requiring invasive JSON overwrites.

## 2026-07-01 (Part 3)
* **Sibling Directory Architecture**: Officially formalized the `repo/`, `workspace/`, and `external/` sibling hierarchy. Nested Git repositories (placing the workspace inside MetaClaw) are strictly forbidden to prevent `git clean` operations from destroying personal data.
* **Streamlined Bootstrapping**: Refactored `setup_plane.sh` and `env_instantiate.py`. The setup process now gracefully pulls `.workspace.template` into the external sibling directory on both local laptops and headless servers automatically.
* **Interactive Pipeling Bug Fix**: Removed interactive `read` commands from the `setup_plane.sh` script to ensure compatibility when the script is piped directly from `curl` into `bash`.

## 2026-07-01 (Part 2)
* **GitOps Agent Development**: Transitioned the `meta-push`, `meta-cmp`, and `meta-pull` staging commands away from legacy local Python synchronization (`bin/meta_sync.py`) to a native GitHub Pull Request workflow, leveraging the newly public MetaClaw repository.
* **Roadmap Update (Routing & Customization)**: Formally documented the limitations of the current opinionated prompt-to-model routing architecture and established Milestone 3: The Modular Routing & Un-opinionated Customization Refactor.

## 2026-07-01
* **Milestone 2 Progress**: Successfully established a headless Tier 2 Control Node (GMKtec K8 Plus). The node successfully boots the OpenClaw gateway, LiteLLM proxy, VictoriaLogs, and PostgreSQL, and responds to prompts, though comprehensive integration testing of all providers remains pending.
* **Tier vs. Plane Decoupling**: Transitioned cluster orchestration from a monolithic "Tier" identity to a decoupled "Tier vs. Plane" architecture. Nodes now assume specific functional roles (Control, Compute, Execution, Archive) which dynamically dictate their provider assignments.
* **Headless Node Lifelines**: Enforced a strict architectural rule where headless nodes run Tailscale on bare-metal (`metal: true`) rather than in Docker. This ensures `factory-reset-soft` does not sever the user's SSH connection.
* **WebCrypto / Secure Context Fix**: Solved a critical infinite login loop caused by modern browser WebCrypto API restrictions. Implemented `tailscale serve` to natively wrap the OpenClaw GUI in an HTTPS certificate, satisfying the browser's "Secure Context" requirements for remote Tailscale IPs.
* **Automated Device Pairing**: Implemented `auto_approve.py`, a schema-aware JSON parser that runs in the background during `make gui` to seamlessly intercept and approve OpenClaw 2026.6.8 device pairing requests.
* **Symlink Context Hardening**: Updated `bin/orchestrate.py` and the root `Makefile` to strictly use physical paths (`os.path.realpath`) when executing Docker Compose commands, preventing relative path resolution errors (e.g., `../../memory/.env`) inside symlinked directories.

## 2026-06-27
* **Release `stable-v1`**: Successfully achieved a stable, working Tier 0 OpenClaw environment.
* **Open Source Repository**: Officially established the public MetaClaw repository at [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw).
* **Housekeeping**: Removed all auto-generated `services/**/index.md` files from version control to prevent merge conflicts. These files are now generated locally via the `make docs` or `make wizard` pipeline.

## 2026-06-20
* **Milestone Achieved**: Successfully transitioned MetaClaw framework development out of external browser-based LLM chats (e.g., gemini.google.com) and moved it natively into the user's local OpenClaw deployment. The OpenClaw software agent now has read/write access to the MetaClaw repository via a mounted workspace and can actively develop the framework.

