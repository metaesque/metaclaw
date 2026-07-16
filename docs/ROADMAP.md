# MetaClaw Roadmap

## Phase 1: Foundation & Infrastructure (Completed)
- [x] Repository structure and Makefiles
- [x] Docker Compose service definitions
- [x] System profiling (`sysprofile.py`) and orchestration (`orchestrate.py`)
- [x] Network mesh via Tailscale
- [x] Hardware power telemetry and baseline mapping (`power_kasa.py`)

## Phase 2: Local AI Independence (In Progress)
- [x] Configure LiteLLM proxy for tiered routing.
- [x] Implement predictive routing to minimize cloud API costs.
- [x] Dynamic Tier 2 configuration generation for Ollama endpoints.
- [ ] **Verify distributed LLM invocation:** Ensure 'control' node routes `simple-model` to local Gemma4 and `medium/complex-model` to the 'compute' node's Llama4 over the local LAN.
- [ ] Verify `0.0.0.0` host bindings for distributed Docker containers.

## Phase 3: Agentic Capabilities (Planned)
- [ ] Browser automation integration (Browser-Use, Stagehand).
- [ ] Memory plane synchronization (pgvector / Milvus).
- [ ] Distributed log aggregation (VictoriaLogs) for cost auditing.
- [ ] OpenClaw UI dashboard deployment.

## Phase 4: Full Automation (Future)
- [ ] Continuous Integration / Autonomous self-repair loops.
- [ ] Zero-trust IAM enforcement across planes.
