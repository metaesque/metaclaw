# turso: Turso

## Overview

Turso is a distributed, edge-hosted database built on libSQL, which is an open-
source fork of SQLite. It is designed to push data as close to the compute layer
as possible, allowing for microsecond read latencies. Turso supports embedded
replicas, meaning an application can read from a local SQLite file while Turso
seamlessly syncs changes to and from a global edge network. It also natively
supports vector embeddings.

For OpenClaw, Turso perfectly aligns with the framework's local-first, node-
based architecture. OpenClaw agents often run on laptops, Raspberry Pis, or VPS
instances. Turso allows an agent to treat its memory as a local SQLite database,
resulting in zero-latency reads and writes for real-time memory processing. When
the agent moves to a different device or spins up a new node, Turso
automatically syncs the agent's memory states, vectors, and operational data.
This gives OpenClaw a unified, geographically distributed memory layer that
maintains the simplicity and speed of a local file system while offering
enterprise-grade semantic search and replication.
