# MEMORY.md - Cluster Metrics
- **EVO-X2 Limits:** 96GB allocatable unified VRAM. Llama 4 109B consumes ~55GB. Monitor closely for Out-Of-Memory (OOM) conditions during context scaling.
- **K8 Plus Limits:** 32GB standard RAM. Contested by PostgreSQL, Redis, LiteLLM, and OpenClaw. Watch for Docker memory pressure.

