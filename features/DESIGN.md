# MetaClaw Features Architecture

Welcome to the MetaClaw Features subsystem. While the `projects/` subsystem in OpenClaw governs autonomous software development tasks, the `features/` directory in MetaClaw is dedicated to the **modular architectural capabilities** of the platform itself.

## Philosophy

MetaClaw is a decentralized, shared-nothing cluster OS. To prevent the core framework from devolving into a monolithic, unmaintainable script, distinct system capabilities (e.g., distributed storage, power monitoring) must be encapsulated into formal "Features."

A Feature is not an agentic task; it is a platform subsystem. Features provide the data, setup scripts, and configurations that the global `Makefile` and root orchestration scripts rely upon.

## Documentation Architecture

Each Feature must be strictly formalized to ensure clarity and maintainability as the cluster scales. Every feature directory (e.g., `features/clawdisk/`) must contain a `docs/` folder with the following structural documents:

1.  **`DESIGN.md`:** The "What & Why". This document explains the scope of the feature, its core functionality, naming conventions, and how it integrates with the rest of MetaClaw.
2.  **`DECISIONS.md`:** Architecture Decision Records (ADRs). This document tracks the engineering choices made during the feature's lifecycle (e.g., why a specific network protocol or kernel mount option was chosen over alternatives).

Unlike the `projects/` subsystem, Features do not require an `AGENTS.md` file, as they are not isolated task spaces for autonomous code generation.

## Implementation Guidelines

*   **Integration over Isolation:** Features live in `features/<name>/`, but they are expected to deeply integrate with MetaClaw. They may introduce custom `make` targets and interact with shared abstract libraries (like `lib/devices.py`).
*   **Encapsulated Executables:** Specific initialization logic for a feature should live in `features/<name>/bin/<name>_setup.py`, which is then invoked by the global cluster setup routines.
