# memcached: Memcached

## Overview

Memcached is a high-performance, distributed memory object caching system
originally intended to speed up dynamic web applications by alleviating database
load. It operates entirely in memory as a simple key-value store, meaning it
lacks any out-of-the-box persistence. If the server reboots or the process
crashes, all stored data is instantly lost.

For OpenClaw agents, Memcached can serve as a highly volatile, ultra-low-latency
scratchpad. An agent might use it to temporarily cache API responses from
external tools (like weather data or fetched web pages) or to store intermediate
step calculations during a complex chain of thought. This prevents the agent
from needlessly re-fetching data during a short-lived execution loop.

However, its utility for true "agent memory" is heavily restricted. Because it
lacks vector search capabilities and data persistence, it cannot handle semantic
recall or retain conversational history across session restarts. It is strictly
a tactical tool for transient execution state rather than a cognitive memory
layer.
