# MetaClaw Changelog

This document records significant changes and updates made to the MetaClaw framework.

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

* **Release `stable-v1`**: Successfully achieved a stable, working Tier 0 OpenClaw
  environment.
* **Open Source Repository**: Officially established the public MetaClaw repository
  at [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw).
* **Housekeeping**: Removed all auto-generated `services/**/index.md` files from
  version control to prevent merge conflicts. These files are now generated locally
  via the `make docs` or `make wizard` pipeline.

## 2026-06-20

* **Milestone Achieved**: Successfully transitioned MetaClaw framework development
  out of external browser-based LLM chats (e.g., gemini.google.com) and moved it
  natively into the user's local OpenClaw deployment. The OpenClaw software agent
  now has read/write access to the MetaClaw repository via a mounted workspace and
  can actively develop the framework.
