# MEMORY.md - Operational Constraints
- **Hardware Reality:** The EVO-X2 has 96GB of usable VRAM. The Orchestrator and Router consume ~68GB. Visual generation models must be loaded and unloaded dynamically.
- **Concurrency Limit:** You may only authorize ONE visual generation agent (Designer, Artist, or Director) to execute at a time. Do not dispatch parallel image/video rendering tasks.

