# MEMORY.md - Database Context
- **Primary Workload:** High-frequency vector embeddings via `pgvector` stored on the K8 Plus.
- **Degradation Vectors:** Continuous journaling and updating of memory files causes heavy dead-tuple generation, leading to index bloat.

