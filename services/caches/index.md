# Real-Time Cache Overview

## Providers

### Redis
High Utility. Redis is the Swiss Army knife for real-time agent operations. It
provides microsecond latency for session state management, pub/sub for sub-agent
communication, and vector search via Redis Stack. It is easily containerized
alongside an OpenClaw deployment, making it a robust, low-latency engine for
immediate conversational memory.

### Context Lakes
Low Utility (for real-time). Context Lakes are powerful for deep, historical RAG
pipelines, but they are batch-oriented storage architectures rather than real-
time memory caches. They feed the agent's long-term knowledge but do not provide
the fast, transient execution memory required for fluid, real-time agent
interactions.

### Turso
Highest Utility. Turso perfectly bridges OpenClaw's local-first philosophy with
distributed needs. Its libSQL foundation means agents interact with it like a
local file (zero network latency for immediate recall), but it automatically
syncs across all of a user's OpenClaw nodes. The built-in vector support handles
semantic search effortlessly within a highly portable architecture.

### Convex
Moderate/Low Utility. The reactive, TypeScript-native nature of Convex is
excellent, but it fundamentally shifts the architecture to a Cloud-backend
model. OpenClaw agents are typically designed to run close to the metal (or in
local containers). Relying on Convex moves the memory core to a centralized
cloud, which may violate privacy or local-execution preferences.

### Memcached
Lowest Utility. While incredibly fast, Memcached's complete lack of persistence
and zero support for vector/semantic search makes it practically useless for LLM
memory. It can only cache API responses; it cannot help an OpenClaw agent recall
past conversations, facts, or concepts.

### Memori Labs
Moderate/High Utility. This technology solves the hardest part of agent memory:
cognitive synthesis. It abstracts entity extraction and memory decay, making the
OpenClaw agent vastly more intelligent out of the box. However, it ranks lower
than Turso and Redis because OpenClaw's current design philosophy leans toward
transparent, file-based (`MEMORY.md`) local control rather than opaque, API-
driven external synthesis.
