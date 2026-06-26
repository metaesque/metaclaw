# postgres: PostgreSQL + pgvector

## Overview

PostgreSQL is a highly stable, open-source relational database provider for the
Memory service. By adding the `pgvector` extension, it gains the ability to
store high-dimensional embeddings and perform exact and approximate nearest
neighbor searches.

For OpenClaw, this provides a unified storage layer where both standard
relational state (like agent configs or parsed data) and semantic memory vectors
can live side-by-side. This eliminates the need to maintain two separate
database systems, simplifying the local deployment architecture for edge nodes.
Its robust querying capabilities allow agents to perform complex hybrid
searches, filtering memories by structured metadata (like dates or source types)
before executing the vector similarity comparison.

<h2 id="diagnostic-checks">Diagnostic Checks (memory postgres)</h2>
1. **Roles:** You should see `litellm_app` and `openclaw_app`
2. **Databases:** You should see `litellm_db` and `openclaw_db`
3. **Extensions:** You should see `vector` version 0.6.0 (or higher)
