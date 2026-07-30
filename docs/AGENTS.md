# OpenClaw Agent Architecture & Runtime Summary

This document synthesizes the core mechanics of how OpenClaw interacts with
agents, builds prompts, routes tasks, and manages context. It is designed to
provide a deep foundational understanding of the agent lifecycle.

---

## 1. The Semantic Ambiguity of "Sub-Agents" vs. "Multi-Agents"

There is a profound and well-documented linguistic ambiguity within the
OpenClaw ecosystem regarding the term "sub-agent." It is critical to
determine which definition applies to your architecture to avoid
catastrophically misconfiguring your agent payloads.

**A. The Official Runtime Sub-Agent (Background Worker)**

1.  **Invocation:** Spawned exclusively via the `sessions_spawn` tool.
2.  **Definition:** A temporary, isolated, non-blocking background thread
    used to execute a single specific task asynchronously.
3.  **Workspace & Files:** It does *not* possess its own physical workspace
    or configuration. It inherits the parent's environment. To save token
    costs and prevent background loops from having identity crises, OpenClaw
    aggressively strip-mines the bootstrap payload. A runtime sub-agent only
    receives `AGENTS.md` and `TOOLS.md`. It will never read a `SOUL.md` or
    `IDENTITY.md`.
4.  **Communication:** Unidirectional. It finishes its task and pushes a
    direct response back to the parent session via the announce chain.

**B. The Multi-Agent Team Member (Inter-Agent Delegation)**

1.  **Invocation:** Delegated to via the `sessions_send` tool.
2.  **Definition:** A permanent, independent, persistent AI persona defined
    in `openclaw.json`. While hierarchically "subordinate," it is a full
    agent.
3.  **Workspace & Files:** Has its own dedicated workspace directory. Because
    it is a true persistent agent, it receives its full bootstrap payload,
    securely loading its own unique `SOUL.md`, `IDENTITY.md`, `USER.md`, and
    full system prompt context.
4.  **Communication:** Bidirectional dialogue between independent personas.

---

## 2. Configuration & Multi-Agent Routing

OpenClaw reads an optional JSON5 config from `~/.openclaw/openclaw.json`.
The Gateway utilizes a "hot reload" watcher that applies safe changes
instantly, while restarting automatically for critical infrastructure
updates (like binding a new port).

**Configuration Scopes:**

1.  **`agents.defaults`:** Sets the shared workspace, model fallbacks,
    sandbox mode, and context limits for all agents.
2.  **`agents.entries.*`:** Overrides the defaults for a specific, named
    agent persona (e.g., assigning a specialized TTS voice or denying
    access to the browser tool).

**Binding Agents to Channels:**

1.  **Match Criteria:** The `bindings` array maps specific conversations to
    an agent using `channel`, `accountId`, and `peer` identification.
2.  **Priority:** Matches are evaluated deterministically, prioritizing exact
    peer matches over channel-wide wildcards.

---

## 3. Workspace Bootstrap & Context Limits

On the first turn of a new session, OpenClaw injects the contents of
specific user-editable Markdown files directly into the system prompt's
Project Context.

**Context Budget Ownership:**

1.  **Bootstrap Limits:** Governed by `bootstrapMaxChars` (default 20k) and
    `bootstrapTotalMaxChars` (default 60k). Truncation notices are injected
    if files exceed these limits.
2.  **Startup Context:** One-shot preludes for `/new` sessions, injecting
    recent daily `memory/*.md` files.
3.  **Context Injection Rules:** Governed by `contextInjection`. The default
    (`continuation-skip`) skips re-injecting the workspace files on safe
    follow-up turns to preserve tokens.

---

## 4. Tool Policy and Sandboxing

Each agent in a multi-agent setup can override the global sandbox and tool
policy, allowing you to run a highly privileged control agent alongside a
locked-down public agent.

**Tool Restriction Precedence:**

1.  **Profiles:** `tools.profile` establishes the baseline (e.g., `coding`
    or `messaging`).
2.  **Global Policy:** `tools.allow` and `tools.deny` apply global filters.
3.  **Agent Policy:** `agents.entries.*.tools.allow` applies agent-specific
    filters.
4.  **Sandbox Policy:** Context-specific denials (e.g., stripping gateway
    tools from sub-agents) are applied last.

**Sandbox Scopes:**

1.  **`session`:** One isolated container and workspace per session.
2.  **`agent`:** One container per agent ID (the default).
3.  **`shared`:** A single shared container across multiple agents.

---

## 5. Execution Models: Sub-Agents, Swarm, and ACP

OpenClaw provides distinct execution models for delegating background work
and interacting with external coding harnesses.

**Native Sub-Agents:**

1.  **Invocation:** Spawned via `sessions_spawn`. They run on the local
    Gateway's sub-agent concurrency lane.
2.  **Isolation:** They start with a clean child transcript (`isolated`) by
    default to save tokens, though they can `fork` the parent context if
    nuanced historical instructions are required.
3.  **Delivery:** They report back to the parent session via an internal
    announce event. The parent should use `sessions_yield` to wait for this
    event rather than polling.

**Swarm Orchestration:**

1.  **Definition:** An experimental Code Mode feature allowing JavaScript
    control flow (`Promise.all`, `while`) to orchestrate many sub-agents.
2.  **Behavior:** Children act as "collector" leaves, returning structured
    JSON results rather than announcing text back to a chat channel.

**Agent Client Protocol (ACP):**

1.  **Definition:** Allows OpenClaw to run external coding harnesses
    (Claude Code, Cursor, Copilot) using the `acpx` plugin backend.
2.  **Spawning:** Invoked via `/acp spawn` or `sessions_spawn` using
    `runtime: "acp"`. Sessions can be `oneshot` or `persistent`, and can
    bind directly to the current chat thread.
3.  **Permissions:** ACP sessions run non-interactively and rely on strict
    `permissionMode` configs (e.g., `approve-all` or `approve-reads`) to
    manage file writes without hanging on TTY prompts.

---

## 6. Goals, Steering, and CLI Execution

OpenClaw supports long-running state management and out-of-band execution.

**Goals:**

1.  **Definition:** A durable, session-bound objective that survives
    restarts. Created via `/goal start <objective>`.
2.  **Budgets:** Goals can have an optional token budget. When exceeded, the
    goal pauses (`budget_limited`) until manually resumed by the operator.

**Steering:**

1.  **Usage:** The `/steer` command injects guidance into an already-active
    run at the next supported runtime boundary.
2.  **Queue Modes:** Configured via `queue.mode`, inbound messages can
    `steer` (inject), `followup` (wait in queue), or `interrupt` (abort)
    the active runs.

**CLI Agent Send:**

1.  **Usage:** `openclaw agent --message "..."` allows you to run a single
    agent turn from the command line for programmatic delivery.
2.  **Delivery:** You can target specific session keys, files, and channels
    directly via flags (e.g., `--deliver --reply-channel slack`).
