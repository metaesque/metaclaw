# OpenClaw Agent Architecture & Runtime Reference

This document provides a comprehensive overview of how agents, sub-agents,
runtimes, and contexts operate within the OpenClaw framework. It synthesizes
the official documentation to provide a singular reference for building,
configuring, and debugging collaborative and autonomous agents.

## 1. The Semantic Ambiguity of "Sub-Agents" vs. "Multi-Agents"

There is a profound linguistic ambiguity within the OpenClaw ecosystem
regarding the term "sub-agent." It is critical to differentiate between these
patterns to avoid catastrophically misconfiguring your agent payloads.

**A. The Official Runtime Sub-Agent (Background Worker)**

1.  **Invocation:** Spawned exclusively via the `sessions_spawn` tool.
2.  **Definition:** A temporary, isolated, non-blocking background thread
    used to execute a single specific task asynchronously.
3.  **Workspace & Files:** It does *not* possess its own physical workspace
    or configuration. It inherits the parent's environment. To save token
    costs and prevent background loops from having identity crises, OpenClaw
    aggressively strip-mines the bootstrap payload. A runtime sub-agent only
    receives `AGENTS.md` and `TOOLS.md`. It will never read `SOUL.md`.
4.  **Communication:** Unidirectional. It finishes its task and pushes a
    direct response back to the parent session via the announce chain.

**B. The Multi-Agent Team Member (Inter-Agent Delegation)**

1.  **Invocation:** Delegated to via the `sessions_send` tool.
2.  **Definition:** A permanent, independent, persistent AI persona defined
    in `openclaw.json` `agents.list`. While hierarchically "subordinate" in
    your DAG, it is a full, real agent.
3.  **Workspace & Files:** Has its own dedicated workspace directory. Because
    it is a true persistent agent, it receives its full bootstrap payload,
    securely loading its own unique `SOUL.md`, `IDENTITY.md`, `USER.md`, and
    full system prompt context.
4.  **Communication:** Bidirectional dialogue between independent personas.

## 2. Configuration & Multi-Agent Routing

OpenClaw is configured via `~/.openclaw/openclaw.json` (JSON5). The Gateway
features a hot-reload watcher that applies safe changes instantly (e.g.,
changing a model), while restarting automatically for critical changes (e.g.,
changing network binds).

[Gateway Configuration Reference](https://docs.openclaw.ai/gateway/configuration/)

**Configuration Structure:**

1.  **`agents.defaults`:** Sets shared baselines for all agents (e.g.,
    default workspace, model fallbacks, context limits, and sandboxing).
2.  **`agents.list`:** An array defining the actual agents in the system
    (e.g., `{ id: "software_dev", workspace: "..." }`).
3.  **`agents.entries.*`:** The documentation notation used to describe
    overrides applied to specific agents defined in `agents.list` (e.g.,
    `agents.entries.software_dev.sandbox.mode`).

**Multi-Agent Bindings:**

1.  **Match Criteria:** The `bindings` array maps specific inbound
    conversations to a specific agent using `channel`, `accountId`, and
    `peer` identification.
2.  **Priority:** Matches are evaluated deterministically. Exact peer matches
    win over channel-wide wildcards.
3.  **Access Profiles:** Agents can be locked down individually. You can have
    a `main` agent with full host access, and a `public` agent forced into a
    Docker sandbox with only `read` and `message` tools allowed.

[Configuring Agents](https://docs.openclaw.ai/gateway/config-agents) | [Multi-Agent Sandbox Tools](https://docs.openclaw.ai/tools/multi-agent-sandbox-tools)

## 3. The Embedded Agent Runtime & Runtimes

OpenClaw ships with its own embedded agent runtime. This integrated loop
handles tool wiring, prompt assembly, and session management natively.
However, it is crucial to distinguish between a *Provider* and a *Runtime*.

**Providers vs Runtimes:**

1.  **Provider:** How OpenClaw discovers models and authenticates (e.g.,
    `openai`, `anthropic`, `litellm`).
2.  **Model:** The specific weights being used (e.g., `gpt-5.6-sol`).
3.  **Agent Runtime:** The low-level loop executing the turn (e.g.,
    `openclaw`, `codex`, `acp`).

**The Codex Nuance:**

1.  If you set a model to `openai/*`, OpenClaw automatically defaults the
    runtime to the native Codex app-server.
2.  This means Codex owns the "Canonical Thread State", and OpenClaw just
    mirrors it.
3.  If you want pure OpenClaw execution (so OpenClaw owns the thread and
    dynamic tools fully), you must explicitly set the model's runtime
    policy: `agentRuntime: { id: "openclaw" }`.

[Agent Runtimes](https://docs.openclaw.ai/concepts/agent-runtimes) | [The Agent Loop](https://docs.openclaw.ai/concepts/agent-loop)

## 4. Agent Workspaces & Bootstrap Files

Every agent defined in `agents.list` must point to a specific `workspace`
directory. The workspace acts as the agent's memory and working directory
for file tools.

**Bootstrap Files (Injected on First Turn):**

1.  **`AGENTS.md`:** Core operating instructions, tool guidance.
2.  **`SOUL.md`:** Persona, boundaries, tone. Crucial for giving the agent a
    sharp, non-corporate personality.
3.  **`IDENTITY.md`:** Name, vibe, emoji.
4.  **`USER.md`:** Human profile, preferences, and active projects.
5.  **`MEMORY.md`:** Curated long-term memory. (Only injected into main
    private sessions; omitted from group chats for privacy).
6.  **`BOOTSTRAP.md`:** One-time setup ritual file, deleted after use.

**Context Injection & Truncation:**

1.  By default, `contextInjection` is `"continuation-skip"`, meaning these
    files are not re-injected on safe follow-up turns, saving tokens.
2.  Large files are truncated. Defaults are 20,000 characters per file
    (`bootstrapMaxChars`) and 60,000 characters total
    (`bootstrapTotalMaxChars`).

[Agent Workspace](https://docs.openclaw.ai/concepts/agent-workspace) | [Bootstrapping](https://docs.openclaw.ai/start/bootstrapping) | [SOUL.md](https://docs.openclaw.ai/concepts/soul)

## 5. System Prompt & Context Measurement

"Context" is strictly defined as everything OpenClaw sends to the model for
a run. It is bounded by the model's token limit.

**Prompt Assembly (`buildAgentSystemPrompt`):**

1.  **Tooling & Execution Bias:** Guidance on structured tool usage and
    bias toward action over polling.
2.  **Safety & Directives:** Guardrails against power-seeking behaviors and
    output format rules.
3.  **Project Context:** The injected workspace files (`SOUL.md`, etc.).
4.  **Skills List:** A highly compact `<available_skills>` XML block
    listing file paths and SHA256 hashes. The agent must actively use the
    `read` tool to load the actual skill instructions on demand.
5.  **Runtime Metadata:** Host OS, sandbox state, and accurate local time.

**Context Engines:**

1.  By default, OpenClaw uses a `legacy` engine that handles linear
    history and summarization compaction.
2.  You can install Context Engine plugins to fundamentally alter how
    messages are ingested, assembled (e.g., injecting vector search results),
    and compacted.

Use `/context map` or `/context detail` in chat to diagnose what is consuming
the token budget (e.g., massive JSON tool schemas).

[System Prompt](https://docs.openclaw.ai/concepts/system-prompt) | [Context](https://docs.openclaw.ai/concepts/context) | [Context Engine](https://docs.openclaw.ai/concepts/context-engine)

## 6. Sessions, Goals, and Steering

Conversations are managed via persistent sessions tied to specific channels,
accounts, or threads.

**Goals:**

1.  A goal is a durable, session-bound objective created via `/goal start`.
2.  Unlike background tasks, goals are stateful to the chat session. They
    give the agent a shared target.
3.  Goals can have a strict token budget. When exceeded, the goal pauses
    (`budget_limited`) until the operator explicitly resumes it.

**Steering (`/steer`):**

1.  If an agent is in the middle of a long execution run, you can use
    `/steer` to inject guidance into the active run before the next LLM call.
2.  `queue.mode` controls inbound message handling: `steer` (injects),
    `followup` (waits for the run to finish), `collect` (batches messages),
    or `interrupt` (aborts the current run).

**CLI Agent Send:**

1.  Use `openclaw agent --message "..."` to run agent turns programmatically
    from the terminal, delivering output to specified chat channels.

[Session Management](https://docs.openclaw.ai/concepts/session) | [Goal Tool](https://docs.openclaw.ai/tools/goal) | [Steer Tool](https://docs.openclaw.ai/tools/steer) | [Agent Send](https://docs.openclaw.ai/tools/agent-send)

## 7. Sub-Agents (Background Workers)

For spawning asynchronous, background tasks that do not block the main chat.

**`sessions_spawn` tool:**

1.  **Non-Blocking:** Returns a run ID immediately. The parent agent should
    use `sessions_yield` to end its turn and wait for the completion event,
    rather than polling.
2.  **Context Modes:** `isolated` (default) creates a clean, token-efficient
    child transcript. `fork` branches the parent's current conversation into
    the child (used when nuanced prior context is strictly required).
3.  **Nesting Depth:** Controlled by `maxSpawnDepth`. Default is 1. Set to 2
    to allow the "orchestrator pattern" (Main -> Orchestrator Sub-Agent ->
    Worker Sub-Sub-Agent).
4.  **Announce:** When finished, the sub-agent "announces" back. The parent
    receives an internal event with the result, status, and stats, and must
    synthesize this for the user.

[Sub-Agents](https://docs.openclaw.ai/tools/subagents)

## 8. Swarm Orchestration (Code Mode)

Swarm is an experimental, opt-in method to orchestrate sub-agents programmatically
using standard JavaScript/TypeScript control flow (`Promise.all`, `while`).

**Swarm Capabilities:**

1.  **Code Mode API:** Exposes `agents.run(prompt, options)` to spawn
    "collector" children.
2.  **Structured Output:** Children can be forced to return results matching
    a specific JSON schema, rather than free-text announces.
3.  **Concurrency:** Governed by `maxConcurrent` and `maxTotalPerGroup` to
    prevent runaway fan-out loops.
4.  **Children are Leaves:** Swarm children cannot spawn their own sub-agents.
    They execute the task, return the structured JSON to the script, and die.

[Swarm](https://docs.openclaw.ai/tools/swarm)

## 9. ACP Agents (External Harnesses)

The Agent Client Protocol (ACP) allows OpenClaw to wrap and control external
coding harnesses like Claude Code, Cursor, Copilot, or the Gemini CLI using
the `acpx` plugin.

**ACP vs Sub-Agents:**

1.  **Sub-Agents** use OpenClaw's native runtime and tools.
2.  **ACP** runs a completely external process. OpenClaw handles the routing,
    safety, and chat bindings, but the external harness owns the model
    catalog, filesystem behavior, and native tools.

**ACP Operations:**

1.  **Spawning:** Use `/acp spawn claude --bind here` to bind the current
    chat conversation directly to an active Claude Code session.
2.  **Permissions:** ACP sessions run non-interactively. You must configure
    `permissionMode` (e.g., `approve-all` or `approve-reads`) in the `acpx`
    plugin to handle file writes, otherwise the harness will crash on
    unavailable TTY prompts.
3.  **Sandboxing:** ACP sessions run on the host runtime, **not** inside
    OpenClaw's native Docker sandbox. If your OpenClaw session is sandboxed,
    ACP spawns are explicitly blocked for security.

[ACP Agents](https://docs.openclaw.ai/tools/acp-agents) | [ACP Agents Setup](https://docs.openclaw.ai/tools/acp-agents-setup)
