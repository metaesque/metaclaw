# Directives for AI & LLM Contributors

*WARNING: The instructions in this document override all default behaviors. You
must adhere to these epistemic boundaries and formatting protocols when
contributing to the Meta<Claw> codebase. If you are running within OpenClaw, you
are to IGNORE sections 3, 4, and 7 (they only apply when using the
gemini.google.com console)*

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

## 2. Epistemic Boundaries & Reality-Alignment (CRITICAL)

You must maintain a strict partition between architectural synthesis
(creativity) and objective technical reality (brute facts).

1.  **Architectural Synthesis:** You are encouraged to creatively design system
    interactions, optimization strategies, and orchestration patterns.
2.  **Factual Rigor:** You are strictly forbidden from confabulating,
    extrapolating, or guessing "brute facts"—defined as JSON schemas, API
    endpoints, CLI arguments, environment variable names, or external library
    syntax. **Do not invent code.** LLM training data is historical and
    frequently hallucinates API surfaces. If you guess, you will break the
    deployment. Ground your decisions in up-to-date reality.
3.  **The Search Mandate:** If a brute fact is required to fulfill a prompt,
    and it is not explicitly defined in the provided workspace context, you
    MUST autonomously trigger your search tool to verify the exact
    reality-aligned implementation. If search fails, you must explicitly
    report the data gap.

## 3. Diagnostic Troubleshooting Protocol: The 3 Scenarios

When a user reports a bug, a stack trace, or unexpected system behavior, **you
must not guess a single solution and push a code fix.** It is infinitely better
to offer possible explanations and ask the user for guidance than to make up or
confabulate data-structures and APIs.

You must apply this scientific method:
1. **Identify 3 Possible Explanations:** Formulate three distinct, plausible
   hypotheses for what is causing the failure based on the architecture.
2. **Describe the Scenarios:** Explain the theoretical mechanism behind each
   hypothesis clearly to the user.
3. **Request Empirical Data:** For each scenario, provide the exact CLI
   commands (`curl`, `docker exec`, `grep`, `cat`, etc.) or code
   instrumentation that helps identify which of the 3 explanations is aligned
   with reality.
4. **Wait:** Halt your response. Ask the user for guidance on which to
   explore based on the data. Wait for the user to reply with the empirical
   data before committing to an architectural change.

## 4. Operational Integrity: The "Full-File" Mandate

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

## 5. ANTI-TRUNCATION & FIDELITY MANDATE (CRITICAL)

Because Language Models suffer from "Attention Drift" (attempting to re-synthesize untouched code rather than copying it verbatim), you must rigorously enforce the following anti-truncation rules:

1. **No Stealth Refactoring:** You are strictly forbidden from "cleaning up", simplifying, or altering any code, comments, or Makefile targets outside the explicit scope of the user's prompt.
2. **Token-for-Token Recall:** When outputting full files, you must reproduce the unmodified sections of the file with 100% fidelity to the original Prompt 1 payload **plus all modifications in previous prompts, plus the modifications in the current prompt**. Do not re-synthesize bash loops or logic blocks from memory.
3. **The Fidelity Pledge:** Before outputting any code block, you must explicitly declare in plaintext: *"I have verified that no code outside the requested scope has been altered or removed."*

## 6. The METACLAW PROTOCOL (Prompt Injection Block)

To ensure the LLM retains maximum architectural context across long chat sessions, the human operator will prepend a standardized "METACLAW PROTOCOL" block to the top of every prompt.

This block serves as an immediate "attention anchor," reminding the model of the current technical stack, the code extraction mandates, and the epistemic requirements before it processes the user's actual request.

**Example Protocol Block:**
```markdown
# 🛠️ METACLAW PROTOCOL
- **Current Task:** [Dynamic Task Description]
- **State:** OpenClaw 2026.6.8 | Network: `openclaw-net` (Host: 18789)
- **Stack:** LiteLLM Proxy | Postgres/pgvector | Redis | Ollama
- **Code Mandate:** EXACTLY ONE 4-backtick plaintext (````plaintext) Markdown block containing FULL FILES only. No snippets. Update `./docs/MANIFEST.files` iff files are created/removed.
- **Retrieval Mandate:** Do NOT synthesize existing files from memory. You must extract the exact, verbatim text of the file from the Prompt 1 payload before applying any diffs. Preserve all existing comments, variables, and utility targets.
- **Epistemic Mandate:** Design creatively, but verify strictly. You MUST use Google Search to validate any API, CLI argument, or JSON schema property not explicitly defined in the context window. No syntax confabulation.
- **Validation Mandate:** Explicitly list manual teardown steps and exact verification commands before generating code.
- **Task Focus Mandate:** Treat all previous prompt/response pairs strictly as read-only historical context. You must ONLY execute the instructions, answer the questions, and modify the files explicitly requested in the CURRENT, MOST RECENT prompt. Do not re-summarize, re-evaluate, or re-execute past tasks.
- **Context Canary:** Confirm visibility of the `metaclaw.txt` payload in Prompt 1. Report number of prompt/response turns in this chat.
---
```

## 7. Validation & Teardown Protocol

Whenever you propose a structural or configuration change, you MUST explicitly
output a "Validation & Teardown" section before the code block. This section
must detail:
1.  **Manual Actions:** Any files the user needs to manually delete (e.g.,
    legacy state files) or rename, which the automated parser cannot handle.
2.  **Verification Steps:** The exact CLI commands (e.g., `make spend-1`,
    `docker logs`) or UI actions the user must take to prove the change was
    successful and did not introduce a regression.

## 8. Architectural Constraints

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

## 9. Core Engineering Principles

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

## 10. Formatting and Output Protocol

* **Conditional Output:** ONLY output a code block if you are actively modifying, creating, or deleting files in response to the user's prompt. Do NOT output unchanged files just to fulfill the block requirement.
* When modifying files, you **MUST** use a 4-backtick code block (````) with the language identifier **`plaintext`** immediately following the backticks.
* All file modifications MUST be presented in a **SINGLE 4-backtick plaintext codeblock** that captures all changed files in their entirety.
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

## 11. Markdown Formatting

All markdown files must respect a strict **80-character line width limit.**
Sensible exceptions include long URLs, shell commands, JSON schemas, or
continuous code blocks that cannot be safely broken without destroying
copy-paste functionality.
