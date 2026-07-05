# MetaClaw OpenClaw Session Kickoff (OC.md)

We are beginning a new development session for the MetaClaw framework.

## Working Directory
- Your target repository is located at: `/root/.openclaw/workspace/src/metaclaw`
- You must prepend this absolute path to all relative file paths cited during this session.

## The Staging vs. Root Boundary
- You do *not* have access to the true root (`/Users/wmh/src/wmh/src/thirdparty/metaclaw`).
- You operate *only* within the staging directory (`workspace/src/metaclaw`).
- Changes you make here will later be synced to the root by the human using `make meta-pull`.

## MetaClaw Documentation Topology

To optimize your context window and prevent token bloat, MetaClaw documentation is distributed hierarchically. Use your `read_file` or `search` tools to retrieve deeper context based on this index:

* **Level 1: System Invariants & Topography**
  * `docs/ARCHITECTURE.md`: Read this for deep operational rules, networking standards, cluster provisioning steps, and routing philosophy.
* **Level 2: Roles, Scale & Registry**
  * `docs/PLANES.md`: Read this to understand the 4 functional roles (Control, Compute, Execution, Archive) and their specific hardware configurations.
  * `docs/TIERS.md`: Read this to understand the architectural scale stages (Tier 0 to Tier 4) and how a cluster grows.
  * `docs/SERVICES.md`: Read this for the canonical registry of all supported services and providers (e.g., which Web Fetcher or Sandbox is used).
* **Level 3: Operations & Strategy**
  * `docs/HOWTO.md`: Read this for Standard Operating Procedures (SOPs) like remote Tailscale access, Git recovery, and cluster restarts.
  * `docs/ROADMAP.md`: Read this to understand current development priorities and the strategic roadmap.

## Environment Variables & Secrets
- Because the staging directory is populated by `make meta-push`, some files are missing. Notably, instantiated `services/*/*/.env` files may not exist in staging.
- Do *not* attempt to globally instantiate all secrets in the staging directory via `bin/env_instantiate.py`.
- If you need to test a specific container, manually construct a minimal `.env` file for that service in staging using dummy keys, rather than cloning production secrets.

## Operational Rules & Safety for this Session

1. **Never Execute Destructive Host Lifecycle Targets:** Do NOT run `make factory-reset`, `make factory-reset-soft`, `make factory-reset-hard`, `make clean-state`, `make meta-down`, or any target that completely tears down the Gateway or the network. Doing so destroys the OpenClaw container you are currently running in (suicide).
2. **Container Restarts & The Human-in-the-Loop Loop:** Modifying files inside a running container via `docker exec` does not persist those changes to the MetaClaw codebase. Update the source files in the staging directory, then instruct the human to execute `make meta-pull` followed by the appropriate `make apply` target.
3. **Docker in Docker:** When using your `execute_shell_command` tool, you are calling Docker from within the OpenClaw Sandbox container (which mounts the host's Docker socket). You can use `docker ps` and `docker exec` normally to troubleshoot.
4. **Test Your Work:** Before telling me a task is complete, use your shell execution tool to run syntax checks or test your code inside the sandbox.

Acknowledge you have ingested the context files and are ready for the first task.
