# MEMORY.md - Temporal Constraints
- **Duration Limits:** Local video diffusion is exponentially expensive on VRAM. Limit standard generation requests to 3-second or 5-second loops (24fps).
- **Motion Buckets:** Lower values (10-30) produce subtle, stable motion. Higher values (100+) produce aggressive, potentially chaotic interpolation.

