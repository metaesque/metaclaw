# redis: Redis

## Overview

Redis is an advanced, in-memory data structure provider that supports complex
data types such as strings, hashes, lists, sets, and sorted sets. Unlike
Memcached, Redis offers configurable persistence (saving to disk) and has a rich
ecosystem of modules. Notably, Redis Stack introduces RedisVL (Vector Library),
which allows it to store embeddings and perform semantic similarity searches.

Within OpenClaw, Redis is highly versatile for managing real-time agent state.
The lists and hashes are ideal for maintaining a rolling window of recent
conversational context, allowing the agent to instantly read the last few turns
of dialogue without parsing local disk files. Furthermore, its pub/sub messaging
capabilities can be used to coordinate multiple sub-agents operating
concurrently within the OpenClaw environment.

By utilizing Redis as a vector store provider, OpenClaw can index its local
`MEMORY.md` and transcript files in real-time. When a user asks a question
requiring historical context, the agent can perform a sub-millisecond semantic
search against the Redis cache to retrieve the exact relevant memories,
providing a highly responsive and persistent cognitive loop.

<h2 id="diagnostic-checks">Diagnostic Checks (cache redis)</h2>
1. **Connectivity:** You should see `PONG`
2. **Max Memory:** You should see `512.00M`
3. **Eviction Policy:** You should see `allkeys-lru`
