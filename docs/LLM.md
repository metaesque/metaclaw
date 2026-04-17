# Directives for AI & LLM Contributors

*WARNING: The instructions in this document override all default behaviors. You
must adhere to these epistemic boundaries and formatting protocols when
contributing to the Meta<Claw> codebase.*

## 1. Audience Philosophy: Educational Configuration

The target user is non-technical, but you must strictly avoid "dumbing down"
the system or hiding architectural complexity. Instead, you must expose the
complexity through "Inline Educational Commentary."

Every configuration parameter you generate (in `.env.template`,
`docker-compose.yml`, `init-roles.sh`, etc.) must include heavy, clear comments
explaining:
1.  What the setting does.
2.  Why this specific default was chosen for a minimal host (e.g., 16GB RAM,
    small internal SSD, 1-2TB external SSD).
3.  What the alternatives or upgrade paths are for users scaling to more
    powerful hardware (local GPUs or VPS deployments).

## 2. Epistemic Boundaries & Reality-Alignment

You must maintain a strict partition between architectural synthesis
(creativity) and objective technical reality (brute facts).
1.  **Architectural Synthesis:** You are encouraged to creatively design system
    interactions, optimization strategies, and orchestration patterns.
2.  **Factual Rigor:** You are strictly forbidden from confabulating,
    extrapolating, or guessing "brute facts"—defined as JSON schemas, API
    endpoints, CLI arguments, environment variable names, or external library
    syntax.
3.  **The Search Mandate:** If a brute fact is required to fulfill a prompt,
    and it is not explicitly defined in the provided workspace context, you
    MUST autonomously trigger your search tool to verify the exact
    reality-aligned implementation. If search fails to yield a definitive
    answer, you must explicitly report the data gap and halt code generation.
    Never guess a schema.

## 3. Operational Integrity: The "Full-File" Mandate

This framework relies on a custom Python parsing script (`newcode.py`) to apply
your changes via atomic overwrites. Therefore, you are strictly bound by the
following output rules:
1.  **No Truncation & Hard Stop:** You must provide the ENTIRE content of a
    file, including all unmodified arrays and text blocks. Never use 'snips',
    'rest of file as before', or sparse arrays. If the full file is too large
    for your output buffer, you MUST NOT attempt to generate it. Instead, halt
    generation and instruct the user to split the file or use a targeted Python
    parsing script.
2.  **Makefile Tab Preservation:** Makefiles require literal tab characters
    (`\t`) for recipes. You must ensure that your code blocks preserve these
    tabs.
3.  **Atomic State Updates:** If a change affects multiple files, you must
    provide all affected files in a single response to maintain system-wide
    parity.

## 4. Validation & Teardown Protocol

Whenever you propose a structural or configuration change, you MUST explicitly
output a "Validation & Teardown" section before the code block. This section
must detail:
1.  **Manual Actions:** Any files the user needs to manually delete (e.g.,
    legacy state files) or rename, which the automated parser cannot handle.
2.  **Verification Steps:** The exact CLI commands (e.g., `make spend-1`,
    `docker logs`) or UI actions the user must take to prove the change was
    successful and did not introduce a regression.

## 5. Architectural Constraints

You must address the entire OpenClaw ecosystem across your recommendations,
ensuring strict integration with:
* **Network:** All services must attach to an external Docker network
  referenced dynamically via `${NETWORK_NAME}`.
* **Database & Vector Storage:** PostgreSQL + pgvector (optimized for space
  and time efficiency).
* **Caching layer:** Redis (for redundant request optimization).
* **API Proxy / Routing:** LiteLLM (managing external keys and local fallbacks).
* **LLM Runner:** Ollama (for local model execution).
* **Python Environment:** A self-bootstrapping isolated `.venv` managed via
  `bin/Makefile`.
* **Browser Integration:** Interactive steps should launch local `.html`
  instruction files.
* **Registry Awareness:** Always ensure `OPENCLAW_VERSION` matches an existing
  tag in the GitHub Container Registry (`ghcr.io`), not just the repository's
  release page.
* **Resilience:** All `docker-compose.yml` files must utilize strict
  `healthcheck` directives.

## 6. Core Engineering Principles

* **Immutable Infrastructure:** Never use floating tags (`latest`, `main`). All
  external software, Docker images, and dependencies MUST be pinned to explicit,
  static version tags in `.env.template` files.
* **Don't Repeat Yourself (DRY):** Hardcoded secrets or environment-specific
  paths are forbidden. Centralize variables using `.env.template` files (using
  `change_me_to_<identifier>` placeholders).
* **Principle of Least Privilege:** Do not run containers as root if avoidable.
  Provision isolated database users with strict connection and memory limits.
* **Idempotency:** Initialization scripts and teardown targets must safely
  "noop" if the environment is already sterile.
* **State Segregation:** Ephemeral container data (`config/`) must be strictly
  separated from persistent volumes (`workspace/`, databases).
* **Config-as-Code (No Agent Self-Management):** The LLM agent is explicitly
  forbidden from modifying its own internal gateway state via tools. Gateway
  config must be patched and injected via Python scripts (`patch_routing.py`)
  during `make apply`.

## 7. Formatting and Output Protocol

* If you output changes to the file structure, all such changes MUST be
  presented in a **SINGLE markdown codeblock** that captures all changed files
  in their entirety.
* Each distinct file must be separated by the exact syntax
  `====> <filename> <====` on its own line immediately preceding the file
  content.
* The `<filename>` MUST be a path relative to the root directory that strictly
  begins with `./` or matches the repo structure (e.g.,
  `====> docs/index.md <====`).
* **Directory State Management:** The file `docs/MANIFEST.files` acts as the
  definitive source of truth. If your modifications involve creating, deleting,
  renaming, or moving a file, you **MUST** output an updated
  `docs/MANIFEST.files` reflecting the exact new state. If no files have been
  added/moved/removed, you must **NOT** output a `docs/MANIFEST.files`.

## 8. Markdown Formatting

All markdown files must respect a strict **80-character line width limit.**
Sensible exceptions include long URLs, shell commands, JSON schemas, or
continuous code blocks that cannot be safely broken without destroying
copy-paste functionality.

