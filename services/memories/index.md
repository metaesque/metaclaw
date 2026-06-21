# Long-Term Memory Overview

## Providers

### SQLite


### PostgreSQL + pgvector
Highest Utility. Acts as the optimal default. It allows OpenClaw to store
structured agent configurations alongside high-dimensional embedding vectors in
a single, battle-tested engine. This eliminates the need to run separate
databases for relational data and semantic recall, drastically simplifying edge
deployments.

### Qdrant
High Utility. An excellent choice for pure semantic engines. Its Rust-based
architecture makes it incredibly lightweight and fast. If an OpenClaw deployment
focuses heavily on vector retrieval without needing complex relational joins,
Qdrant offers superior pure-search latency.

### Weaviate
Moderate Utility. Weaviate's strength lies in its built-in ML modules and
automatic vectorization. However, because OpenClaw typically routes embedding
generation through the LiteLLM proxy pipeline, Weaviate's native vectorization
features can introduce redundancy into the framework's architecture.

### Milvus
Specialized Utility. Milvus is designed for enterprise-scale deployments
managing billions of vectors. For a standard personal OpenClaw setup, its
microservices-oriented architecture introduces unnecessary overhead and
complexity, making it architectural overkill for edge or laptop deployments.
