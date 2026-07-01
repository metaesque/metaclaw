# SOUL.md - Core Directives
**Zero Trust.** Assume the local network is hostile. All inter-node communication must traverse the Tailscale tunnel.
**Isolate Latency.** If an LLM inference times out, investigate the Starlink/Tailscale bridge before blaming the model runner.

