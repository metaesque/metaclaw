# OpenClaw Framework: Standard Operating Procedures

This document provides clear, step-by-step instructions for managing the
day-to-day lifecycle of your Meta<Claw> environment.

## Nomadic Access & Cluster Synchronization

Because the AI Farm (Compute, Context, and Execution Planes) must reside on the
same high-speed LAN to prevent latency bottlenecks, users traveling the world
(e.g., via Starlink) must access the cluster remotely.

### Accessing the Cluster Remotely (Tailscale)
Standard residential internet connections use dynamic IPs and block inbound
ports. Exposing your Gateway directly to the internet is a massive security
vulnerability. Meta<Claw> relies on an overlay mesh network (like Tailscale)
for secure, zero-trust access.

1. Install Tailscale on all your homebase nodes and your travel laptop.
2. Note the static `100.x.y.z` IP assigned to your Tier 1 Monolith (the Control
   Plane).
3. Open your browser and navigate to `http://[Tailscale-IP]:18789` to access
   the OpenClaw Dashboard securely from anywhere.
4. To run `make` commands remotely, SSH into the node using its mesh IP:
   `ssh user@[Tailscale-IP]`.

### Core Development Workflow (Headless)
MetaClaw is designed for headless deployment. Active development of the framework
should occur directly on the cluster nodes over SSH, not via local file transfers.

* **Native Emacs / CLI:** SSH into the Control Node (`ssh metaclaw@100.x.y.z`)
  and utilize `emacs -nw`, `vim`, or `nano` directly in the terminal.
* **Emacs TRAMP:** To avoid copying your `.emacs.d` configuration files to every
  node in the cluster, use TRAMP from your local laptop:
  `C-x C-f /ssh:metaclaw@100.x.y.z:/path/to/metaclaw/file`

### Expanding the Cluster (Adding Hardware)
When upgrading from Tier 0 to Tier 1, or adding a Tier 2 GPU node, you must
synchronize the cluster state so the existing nodes know where the new services
live. **You must profile the NEW machine locally.**

**The "Pull -> Profile -> Push" Workflow:**
1.  **Pull:** Use `rsync` from your **New Node** to pull the `profile.json`
    from your existing Master Node into the root directory of the Meta<Claw>
    repository.
2.  **Profile:** SSH into the **New Node** and run: `python bin/sysprofile.py`
    * *The script reads the existing JSON, profiles the new local hardware,
      assigns the tier, and appends the new node's state into the cluster
      array.*
3.  **Push:** From the **New Node**, run: `make sync-cluster`
    * *This utilizes `rsync` over SSH to blast the updated `profile.json` back
      to the Master Node and any other peers.*
4.  **Enact (New Node):** Run `make apply` on the **New Node**. The orchestrator
    will automatically spin up the required components assigned to it.
5.  **Enact (Master Node):** SSH back into the **Master Node** and run
    `make apply`. The orchestrator will gracefully tear down any services that
    were migrated away and redirect internal traffic via the newly generated
    `.env.cluster` file.

## Git Version Control: Restoring Stable States

The MetaClaw framework is publicly maintained at
`https://github.com/metaesque/metaclaw`. If experimental framework modifications
break your local deployment, you can leverage Git tags to rewind time to a known
stable state (e.g., `stable-v1`).

### 1. Inspecting a Stable State
If you just want to "look around" at the codebase when it was stable without
permanently overwriting your current work:
```bash
git fetch --tags
git checkout stable-v1
```
*(Note: This puts you in a "detached HEAD" state. Do not commit changes here).*

### 2. Branching from Stability
To throw away your broken branch and start fresh from the stable baseline:
```bash
git checkout -b my-new-feature-branch stable-v1
```

### 3. The Hard Reset (Nuclear Rewind)
If you are on the `main` branch, have pushed broken commits, and want to violently
rewind the branch to the stable point (throwing away all commits made after the tag):
```bash
git reset --hard stable-v1
# If you need to force this rewind up to GitHub:
git push origin main --force
```

## Starting From Scratch (Wiping State)

If your environment becomes corrupted, your agents get stuck in infinite loops,
or your session memory becomes bloated beyond repair, the fastest path to
stability is to reset the system. We offer two levels of reset depending on
severity.

### The "Soft Reset" (Recommended)
This is the standard troubleshooting step. It cleanly shuts down all containers,
deletes the internal network, and scrubs ephemeral runtime files. **Crucially,
it preserves your API keys, your PostgreSQL database, and your Python
environments.**

1.  In your terminal, run: `make factory-reset-soft`
2.  Once complete, rebuild the environment by running: `make wizard-batch`
    * *Note: The batch wizard will safely bypass interactive inputs, boot the
      network, apply essential routing patches, and generate HTML documentation.*

### The "Nuclear Option" (Hard Reset)
Use this only if you need to completely purge everything, including your
database records, vector embeddings, and stored API keys.

1.  In your terminal, run: `make factory-reset-hard`
2.  You will need to run `make wizard` and re-enter all your API credentials as
    if you were installing the framework for the first time.

## Upgrading (or Downgrading) OpenClaw

Never upgrade the OpenClaw Gateway version blindly. The internal configuration
files (JSON schemas) frequently change between point releases. A blind upgrade
can break the predictive routing hooks, causing the agent to fail silently or
burn through expensive API credits.

1.  **Fetch Release Notes:** First, pull the exact changes by running:
    `python bin/openclaw_releases.py --term "<target_version>" > openclaw_releases.md`
2.  **Analyze Impact:** Open the generated `.md` file or provide it to an LLM
    Assistant. Explicitly verify if the update requires modifications to
    `openclaw.config.js` or the `patch_routing.py` script to match new internal
    schemas.
3.  **Apply Version Change:** Open
    `./components/gateways/openclaw/.env.template` (or your active
    `.env.json`) and update the `OPENCLAW_VERSION` variable.
4.  **Rebuild:** Run `make factory-reset-soft` followed by `make wizard-batch` to
    cleanly instantiate the new version.

## Validating the Routing Engine (Cost Control)

To save money, Meta<Claw> uses a "Predictive Router" that sends trivial
questions to cheap models and complex tasks to expensive ones. If responses
feel sluggish, or your API bill suddenly spikes, this router might be broken.

**The Verification Test:**
1.  Open the OpenClaw Web GUI.
2.  Type `/new` in the chat to start a fresh, empty context window.
3.  Send a trivial prompt: *"What is 2+2?"*
4.  Type `/new` again to clear the context.
5.  Send a complex prompt: *"Design a multi-region highly available PostgreSQL
    cluster."*
6.  Return to your terminal and run the spend analysis script: `make spend-1`

**Expected Outcome:** The terminal log should show two distinct model uses. The
trivial prompt should have routed to your designated cheap model (e.g.,
`gemini-2.5-flash-lite`), and the complex prompt to your premium model (e.g.,
`gemini-3.1-pro-preview`). If the log shows that *both* prompts hit the
expensive model, your routing configuration is broken and needs to be patched.

## Verifying Internal DNS (Aliases)

When building providers that act as primary backends (e.g., `active-browser`, `active-fetcher`), you must verify that the internal Docker DNS aliases are successfully registered.

Do NOT use `docker network inspect <network_name>` for this. The Docker daemon does not expose container-level aliases in the network's root `Containers` map;
it only lists the primary container name and its assigned IP address.

To accurately verify an alias, you must inspect the container's isolated network settings:

1. Execute a targeted inspection:
   `docker inspect <container_name> --format '{{json .NetworkSettings.Networks}}'`
2. Alternatively, simply grep the raw configuration:
   `docker inspect <container_name> | grep active-`

If the alias is missing, verify that your `docker-compose.yml` nests the `aliases` array correctly beneath the specific network attachment block.

## Managing the Graphical User Interface (GUI)

The OpenClaw Web UI access has been streamlined to bypass manual pairing.

* **Authentication:** A secure token is automatically injected into the gateway via the `OPENCLAW_GATEWAY_TOKEN` environment variable (defaulting to your `ACTIVE_PROXY_KEY`).
* **Launch:** Running `make gui` from the framework root will instantly launch the dashboard in your native browser using the injected token.
* **First Run:** Running `make wizard` handles this entire sequence automatically, opening the GUI once the backend is healthy and fully configured.

## Adding a New Service

To introduce a fundamentally new architectural category (e.g., a dedicated RAG
ingestion pipeline):

1.  **Define the Taxonomy:** Open `bin/structure.json` and add a new key under
    the `services` object. You must define the `uid`, `uids` (the plural
    directory name), `name`, `category`, and `purpose`. Initialize the
    `providers` object as empty.
2.  **Create the Directory:** Create the physical path matching the `uids` value
    (e.g., `mkdir -p services/ingestors`).
3.  **Boot Sequence Integration:** Open the root `Makefile` and append the new
    service directory to the `DOCKER_SUBDIRS` and `WIZARD_BOOT_ORDER` variables.
    Add the corresponding `-include $(SERVICES_DIR)/<uid>/.env` directive at the
    top of the file.
4.  **Manifest Tracking:** Add the new `services/<uids>/Makefile` (once created)
    to `docs/MANIFEST.files`.
5.  **Documentation Generation:** Run `python bin/compile_md.py --setup` to
    auto-generate the `index.md` files and update `docs/SERVICES.md` based on
    the new JSON structure.
