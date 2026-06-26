# MetaClaw OpenClaw Session Kickoff (OC.md)

We are beginning a new development session for the MetaClaw framework.

## Working Directory

- Your target repository is located at: `/root/.openclaw/workspace/src/metaclaw`

- You must prepend this absolute path to all relative file paths cited during this
  session.

## The Staging vs. Root Boundary

- You do *not* have access to the true root
  (`/Users/wmh/src/wmh/src/thirdparty/metaclaw`).

- You operate *only* within the staging directory (`workspace/src/metaclaw`).

- Changes you make here will later be synced to the root by the human using
  `make meta-pull`.

## Environment Variables & Secrets (.env files)

- Because the staging directory is populated by `make meta-push` based on
  `<root>/docs/MANIFEST.files`, some files are missing. Notably, while
  `<root>/services/*/*/.env.template` files are present, the fully instantiated
  `<root>/services/*/*/.env` files may not exist in staging (even though
  they do in root). This can cause certain `make` targets to fail when tested in
  staging.

- You should *not* attempt to globally instantiate all secrets in the staging
  directory via `bin/env_instantiate.py` because doing so could interactively
  prompt for new keys, leading to split-brain states where the staging
  environment has different credentials than the production root.

- If you need to test a specific container and it fails due to a missing `.env`
  file, use `docker exec` to interact with the *already running* production
  container, or manually construct a minimal `.env` file specifically for the
  service you are testing in staging using dummy keys, rather than cloning
  production secrets.

## MetaClaw Context

- Read and remember the contents of ./docs/SERVICES.md for the duration of this
  session. It defines the core concepts of planes, tiers, services, and
  providers as used in MetaClaw.

## Environment Context

- **Hardware:** MacBook Air (M-series), 16GB RAM, 256GB SSD.

- **Hardware Tier:** Tier 0 (Minilith), lightweight local services, remote LLMs
  (Gemini 3.1 Pro).

- **Execution:** We are running inside Docker via OrbStack.

## Operational Rules & Safety for this Session

1. **Never Execute Destructive Host Lifecycle Targets:** Do NOT run `make
   factory-reset`, `make factory-reset-soft`, `make factory-reset-hard`, `make
   clean-state`, `make meta-down`, or any target that completely tears down the
   Gateway or the network. Doing so destroys the OpenClaw container you are
   currently running in (suicide).

2. **Container Restarts & The Human-in-the-Loop Loop:** While it is technically
   safe for you to execute `docker restart <container>` or `make -C services/...
   restart` to test immediate configuration tweaks (except for the openclaw
   gateway that you reside within), you must remember that **modifying files
   inside a running container via `docker exec` does not persist those changes
   to the MetaClaw codebase.** If you identify a fix (e.g., modifying
   `settings.yml` for SearXNG), you must update the source files (like
   `docker-compose.yml` or creating a custom `settings.yml` payload to map into
   the container via volumes) in the staging directory. Once you have authored
   the fix in staging, instruct the human to execute `make meta-pull` followed
   by the appropriate `make apply` target so the fix is deployed properly into
   production.

3. **Docker in Docker:** When using your `execute_shell_command` tool, you are
   calling Docker from within the OpenClaw Sandbox container (which mounts the
   host's Docker socket). This works exactly the same as calling Docker on the
   host. You can use `docker ps` and `docker exec` normally to troubleshoot.

4. **Test Your Work:** Before telling me a task is complete, use your shell
   execution tool to run syntax checks or test your code inside the sandbox.

Acknowledge you have ingested the context files and are ready for the first
task.
