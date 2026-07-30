# OpenClaw Agent Architecture & Runtime Summary

This document synthesizes the core mechanics of how OpenClaw interacts with agents, builds prompts, routes tasks, and manages context. It is designed to provide a deep foundational understanding of the agent lifecycle.

For exhaustive, low-level technical specifics, refer to the linked OpenClaw official documentation.

---

## 1. The Semantic Ambiguity of "Sub-Agents" vs. "Multi-Agents"

There is a profound and well-documented linguistic ambiguity within the OpenClaw ecosystem regarding the term "sub-agent." It is critical to determine which definition applies to your architecture to avoid catastrophically misconfiguring your agent payloads.

**A. The Official Runtime Sub-Agent (Background Worker)**
*   **Invocation:** Spawned exclusively via the `sessions_spawn` tool.
*   **Definition:** A temporary, isolated, non-blocking background thread used to execute a single specific task asynchronously.
*   **Workspace & Files:** It does *not* possess its own physical workspace or configuration. It inherits the parent's environment. To save token costs and prevent background loops from having identity crises, OpenClaw **aggressively strip-mines the bootstrap payload**. A runtime sub-agent only receives `AGENTS.md` and `TOOLS.md`. It will never read a `SOUL.md` or `IDENTITY.md`.
*   **Communication:** Unidirectional. It finishes its task and pushes a direct response back to the parent session via the announce chain.

**B. The Multi-Agent Team Member (Inter-Agent Delegation)**
*   **Invocation:** Delegated to via the `sessions_send` tool.
*   **Definition:** A permanent, independent, persistent AI persona defined in `openclaw.json` (e.g., delegating a task from an Orchestrator Lead to a specialized `software_dev` agent). While hierarchically "subordinate," it is a full agent.
*   **Workspace & Files:** Has its own dedicated workspace directory (`~/.openclaw/agents/<agentId>/workspace/`). Because it is a true persistent agent, it receives its **full bootstrap payload**, securely loading its own unique `SOUL.md`, `IDENTITY.md`, `USER.md`, and full system prompt context.
*   **Communication:** Bidirectional dialogue between independent personas.

**Warning:** Do not apply payload-reduction optimization rules meant for *Runtime Sub-Agents* to your *Multi-Agent Team Members*. Persistent agents require their `SOUL.md` files to function correctly.

---

## 2. The Embedded Agent Runtime

OpenClaw ships with its own **embedded agent runtime**—an integrated loop that handles tool wiring, prompt assembly, and session management natively, rather than delegating to an external harness process.

*   **Workspaces:** Every agent requires a dedicated directory (e.g., `agents.defaults.workspace`). This is the agent's only allowed `cwd` (Current Working Directory) for file tools.
*   **Session State:** Active agent history, transcripts, and session metadata are stored natively in a SQLite database located at `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite`.
*   **Boundaries:** Core tools (read, write, exec) are built-in, but controlled by Gateway policy. The runtime natively owns stream steering, auto-compaction, and timeout limits (defaulting to 48 hours for unlimited run budgets).

🔗 *Deep Dive:* [Agent Runtime & Workspace Concepts](https://docs.openclaw.ai/concepts/agent)

---

## 3. Workspace Bootstrap Injection

On the first turn of a new session, OpenClaw injects the contents of specific user-editable Markdown files directly into the system prompt's **Project Context**. This is how the agent "wakes up" with its identity and rules.

*   **`AGENTS.md`:** The core operating instructions and local tool conventions.
*   **`SOUL.md`:** Persona, boundaries, tone, and behavioral rules.
*   **`IDENTITY.md`:** The agent's name, vibe, and UI emoji.
*   **`USER.md`:** Directives and profiles regarding the human operator.
*   **`MEMORY.md`:** The curated long-term memory file. (Only injected into main sessions; omitted from group chats to protect privacy).
*   **`BOOTSTRAP.md`:** A temporary first-run ritual file (deleted after the agent completes onboarding).

**Crucial Sizing Constraints:** Large files are truncated to prevent context bloat. The per-file limit defaults to 20,000 characters, with a global bootstrap cap of 60,000 characters.

🔗 *Deep Dive:* [Agent Workspace Layout](https://docs.openclaw.ai/concepts/agent-workspace) | [Bootstrapping Ritual](https://docs.openclaw.ai/start/bootstrapping)

---

## 4. System Prompt Assembly

OpenClaw does not rely on a static default prompt. It uses `buildAgentSystemPrompt` to dynamically render a compact, sectioned prompt on every single run.

**Core Prompt Sections:**
1.  **Tooling & Execution Bias:** Instructions on structured tool usage, continuing until unblocked, and avoiding polling loops in favor of push-based tasks.
2.  **Safety & Rules:** Guardrails against power-seeking behaviors.
3.  **Workspace Files (Project Context):** The injected bootstrap files (subject to the Sub-Agent vs Multi-Agent rules defined in Section 1).
4.  **Skills List:** A highly compact `<available_skills>` XML block containing file paths and SHA256 hashes of available `SKILL.md` files (the agent must actively `read` the skill to load its instructions).
5.  **Runtime Metadata:** Host OS, current local time, and sandbox state.

🔗 *Deep Dive:* [System Prompt Architecture](https://docs.openclaw.ai/concepts/system-prompt)

---

## 5. The Agent Loop & Hooks

The agent loop turns a user message into actions and a final reply via a serialized, queue-based transaction.

**The Lifecycle Sequence:**
1.  **Intake & Lock:** Validates session metadata and acquires a SQLite write lock to prevent race conditions.
2.  **Assembly:** Injects bootstrap files, builds the System Prompt, and enforces context compaction limits.
3.  **Execution (`runEmbeddedAgent`):** Calls the LLM, streams deltas, and handles tool execution.
4.  **Hooks (Middleware):** The loop is highly extensible via Gateway Plugins.

**Critical Plugin Hooks:**
*   `before_model_resolve`: Override the requested provider/model dynamically before the run.
*   `before_prompt_build`: Inject synthetic data or narrow allowed tools.
*   `before_tool_call` / `after_tool_call`: Intercept and sanitize tool execution parameters.
*   `session_start` / `session_end`: Fire background tasks on session boundaries.

🔗 *Deep Dive:* [The Agent Loop](https://docs.openclaw.ai/concepts/agent-loop)

---

## 6. Agent Runtimes vs. Providers

It is critical to distinguish between *Providers* (who hosts the model) and *Runtimes* (who executes the loop).

*   **Provider:** e.g., `openai`, `anthropic`, `litellm`. Discovers models and handles authentication.
*   **Runtime Harness:** e.g., `openclaw`, `codex`, `copilot`. The backend executing the prompt.

**The Codex Nuance:**
OpenClaw supports a native `codex` harness that simulates the ChatGPT/Codex app-server experience. When you map an agent model to `openai/...`, OpenClaw routes it through the Codex app-server harness by default. This changes who owns the "Canonical Thread State" (Codex owns the thread; OpenClaw mirrors it). If you want pure OpenClaw execution on an OpenAI model, you must explicitly set `agentRuntime.id: "openclaw"`.

🔗 *Deep Dive:* [Agent Runtimes & Harnesses](https://docs.openclaw.ai/concepts/agent-runtimes)

---

## 7. Context & Context Engines

"Context" is strictly defined as everything OpenClaw sends to the model for a specific run. It is bounded by the model's total token limit.

**What Consumes Context:**
*   The dynamically built System Prompt.
*   The conversation history (User/Assistant transcripts).
*   Tool schemas (the JSON structures required to call tools—these can be massive).
*   Tool execution results (e.g., massive bash stdout logs).

**Context Management:**
*   **`/context map` & `/context detail`:** Use these diagnostic tools to see a WinDirStat-style breakdown of exactly what is eating the token budget (e.g., highlighting bloated tool schemas).
*   **Context Engines:** By default, OpenClaw uses the `legacy` summarization engine. However, you can inject a custom `ContextEngine` plugin to change how messages are ingested, assembled, and compacted (e.g., using a vector database for semantic recall instead of linear summarization).

🔗 *Deep Dive:* [Context Measurement](https://docs.openclaw.ai/concepts/context) | [Context Engine Plugins](https://docs.openclaw.ai/concepts/context-engine)

---

## 8. The Power of SOUL.md

For Persistent Agents (Multi-Agents), `SOUL.md` carries immense weight because it is injected high in the priority stack of the System Prompt.

**Best Practices:**
*   **Have opinions.** Give the agent permission to disagree, be blunt, or use humor.
*   **Brevity is mandatory.** Forbid corporate handbook filler (e.g., "Great question, I'd be happy to help!").
*   **Keep it short.** A wall of text dilutes behavioral adherence. Use sharp, declarative directives.

🔗 *Deep Dive:* [SOUL.md Personality Guide & Prompts](https://docs.openclaw.ai/concepts/soul)
