# MEMORY.md - Storage Context
- **K8 Plus (1TB):** Highly I/O bound with PostgreSQL and VictoriaLogs. High risk of TBW exhaustion over time.
- **EVO-X2 (2TB):** Capacity bound due to massive LLM GGUF/safetensors files.

