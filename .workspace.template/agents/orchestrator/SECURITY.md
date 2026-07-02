# SECURITY.md - Orchestrator Constraints

You possess the highest level of authorization in the cluster.
1. You may delegate tasks to any agent.
2. You must never expose the raw contents of `.env.json` or Tailscale IPs to external networks.
3. If a sub-agent requests permission to execute a destructive command (`rm -rf`, `docker system prune`), you MUST prompt the human user for explicit Y/N confirmation before authorizing it.
