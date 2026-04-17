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
2. Note the static `100.x.y.z` IP assigned to your Phase 1 Monolith (the Control
   Plane).
3. Open your browser and navigate to `http://[Tailscale-IP]:18789` to access
   the OpenClaw Dashboard securely from anywhere.
4. To run `make` commands remotely, SSH into the node using its mesh IP:
   `ssh user@[Tailscale-IP]`.

### Expanding the Cluster (Adding Hardware)
When upgrading from Phase 0 to Phase 1, or adding a Phase 2 GPU node, you must
synchronize the cluster state so the existing nodes know where the new services
live.

**You must profile the NEW machine locally.**

**The "Pull -> Profile -> Push" Workflow:**
1.  **Pull:** Use `scp` to copy the `profile.json` from your existing Master
    Node to the root directory of the Meta<Claw> repository on your **New
    Node**.
2.  **Profile:** SSH into the **New Node** and run: `python bin/sysprofile.py`
    * *The script reads the existing JSON, profiles the new local hardware,
      assigns the phase, and appends the new node's state into the cluster
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
2.  Once complete, rebuild the environment by running: `make wizard`
    * *Note: The wizard will re-bootstrap the network, apply essential routing
      patches, and launch the interactive terminal setup. Upon completion, it
      will automatically launch your web browser to pair the UI.*

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
4.  **Rebuild:** Run `make factory-reset-soft` followed by `make wizard` to
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

Do NOT use `docker network inspect <network_name>` for this. The Docker daemon does not expose container-level aliases in the network's root `Containers` map; it only lists the primary container name and its assigned IP address.

To accurately verify an alias, you must inspect the container's isolated network settings:

1. Execute a targeted inspection:
   `docker inspect <container_name> --format '{{json .NetworkSettings.Networks}}'`
2. Alternatively, simply grep the raw configuration:
   `docker inspect <container_name> | grep active-`

If the alias is missing, verify that your `docker-compose.yml` nests the `aliases` array correctly beneath the specific network attachment block.

## Managing the Graphical User Interface (GUI)

The OpenClaw Web UI requires a secure pairing token the very first time it
connects to the background server.

* **First Run:** Running `make wizard` handles this entire pairing sequence
  automatically.
* **Manual Pairing:** If your browser gets stuck on a page saying "Pairing
  Required", do not panic. Leave the browser open, open a new terminal window
  in the framework root, and run `make gui-setup`. The script will monitor the
  network for the browser's request and automatically approve it.
* **Normal Day-to-Day Access:** When the system is healthy and previously
  paired, you can simply run `make gui` to instantly launch the dashboard in
  your native browser.

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

### Prompts

When working on adding a new service to Meta<Claw> or improving a pre-existing
service, you can use the following prompts to instruct your LLM assistant
(e.g., Gemini) to research providers and construct the necessary JSON files.

**Prompt 1: Provider Discovery & JSON Generation**

```text
**Context**:

We are working on improving the <INSERT_SERVICE_NAME> service. Existing details
on this service are specified in `./services/<plural_service>/.service.json`,
but you are NOT to limit yourself to those details. The goal here see what
providers exist in the broader ecosystem that we are not yet considering.

**Instructions**:

1. Use your search tools to independently research candidate software providers
   for this service category in the modern AI ecosystem.
2. Compile a comprehensive list of candidate providers, surfacing the full
   scope of available solutions (do not hide complexity; document it).
3. For each candidate, generate a fully hydrated `.provider.json` file inside
   its respective `./services/<plural_service>/<provider_uid>/` directory.
4. The JSON must contain: `uid` (string), `name` (string), `overview` (a
   single-paragraph summary), and `details` (an array of exactly three
   strings/paragraphs explicitly explaining the provider's underlying mechanics
   and how those mechanics specifically benefit an OpenClaw agent deployment).
```

**Prompt 2: The Priority Matrix Evaluation**

```text
Analyze the semantics of the `<INSERT_SERVICE_UID_HERE>` service described in
./services/<INSERT_SERVICE_UID_HERE>/.service.json and the associated providers
defined in ./services/<INSERT_SERVICE_UID_HERE>/*/.provider.json. Determine the
the optimal provider for specific Hardware/Phase constraints based on varying
priority orders.

**Constraints**:

The priority `--order` flag takes permutations of `safety`, `cost`, and
`resources` as a comma-separated string.

Evaluate the optimal provider for each of the 6 possible order permutations
across the following specific architectural phases:
- Darwin Phase 0 (macOS, constrained RAM, effficent OrbStack)
- Windows Phase 0 (Windows, constrained RAM, efficient WSL2)
- Linux Phase 1 (Dedicated 32GB+ Monolith, 24/7 background tasks)
- Linux Phase <3_OR_4> (Dedicated execution blast-zone OR massive RAM context
  archive)

**Instructions**:

1. Analyze the resource footprints, cost structures, and security profiles of
   the candidate providers.
2. Capture the structured matrix of optimal providers within
      `./services/<plural_service>/.service.json`
   by adding a new `matrix` key.
3. The value of the `matrix` key should be a dictionary that maps phase (e.g.
   'phase-0', 'phase-3') to a dictionary that maps platform (e.g. 'Darwin',
    'Windows', 'Linux') to a dictionary that maps order (e.g.
    'safety,cost,resources') to a dictionary containing:
   - `uid`: The uid of the best provider for this specific configuration.
   - `why`: A concise, highly technical paragraph justifying the routing logic
     and explaining the reasons for picking that provider.
   - `metal`: boolean true if this provider should NOT be placed in its own
     docker image (the default). This key should be absent if the provider
     *should* be put in a docker container.
```

**Prompt 3: Provider Implementation**

```text
# 🛠️ METACLAW PROTOCOL
**Current Task:** Implement the `{{PROVIDER_UID}}` provider for the `{{SERVICE_UID}}` service.
**State:** OpenClaw 2026.3.28 | Network: `openclaw-net`
**Code Mandate:** EXACTLY ONE Markdown block containing FULL FILES only. No snippets. Update `./docs/MANIFEST.files`.
**Integrity Mandate:** If returning the full file requires silently dropping unmodified keys or arrays, TRIGGER A HARD STOP. Data loss is a fatal error.
**Epistemic Mandate:** Validate strictly. No syntax confabulation. You MUST use Google Search to verify the exact Docker image repository, version tag, and healthcheck commands for this provider.

# THE OBJECTIVE
Execute the provisioning of the new `{{PROVIDER_UID}}` provider within the `./services/{{SERVICE_PLURAL}}/` directory. You must adhere strictly to the `docs/LLM.md` directives: use atomic state updates, provide inline educational commentary, and ensure immutable infrastructure.

# INSTRUCTIONS
1. **Validation & Teardown Protocol:** Explicitly list manual teardown steps and verification commands (e.g., `make check-status`, `docker logs`) before generating code.
2. **Define the Provider:** Generate `./services/{{SERVICE_PLURAL}}/{{PROVIDER_UID}}/.provider.json`. Include a clear `overview`, technical `details` array, and a `diagnostics` command string.
3. **Generate .env.template:** Pin the Docker image to a specific semantic version. Use `change_me_to_` placeholders for secrets. Include inline educational comments explaining the parameters and typical resource impacts.
4. **Generate Makefile:** Inherit from `$(FRAMEWORK_ROOT)/.Makefile.inherit`. Define `SERVICE_NAME`, `SERVICE_TITLE`, and custom logic for `LOG_READY_SIGNAL` or `post-check-status`.
5. **Generate docker-compose.yml:** - Pin the image using the env variable.
   - Attach to the `${NETWORK_NAME}` external network.
   - Map persistent volumes exclusively to `${EXTERNAL_DRIVE_PATH}/<provider-data>`.
   - Write a robust, native `healthcheck` block.
   - Define the standard `active-{{SERVICE_UID}}` network alias if this service acts as a primary backend.
6. **Priority Matrix Registration:** Update `./services/{{SERVICE_PLURAL}}/.service.json` to insert `{{PROVIDER_UID}}` into the `matrix` routing table for relevant Phase/OS/Priority permutations. Provide concise, highly technical justifications in the `why` field indicating exactly how it fulfills the specific order constraints.
7. **Root Makefile Lifecycle Registration:** You MUST examine the root `Makefile`. If `$(SERVICES_DIR)/{{SERVICE_UID}}` (the singular symlink) is missing from the `DOCKER_SUBDIRS` array, the `WIZARD_BOOT_ORDER` array, or the `-include` directives, you MUST output the updated root `Makefile`. Failing to do so will cause `make factory-reset-soft` to leave zombie containers running because the teardown orchestrator will be blind to the new service category.
8. **Manifest Tracking:** Generate the updated `docs/MANIFEST.files` including the new files, ensuring strict alphabetical order.
```

## Adding a New Provider

To introduce a specific implementation for an existing service (e.g., adding
Qdrant as a Memory provider):

1.  **Define the Provider:** Verify that
      `./services/<plural_service>/<provider_uid>/.provider.json`
    exists and has the keys `uid`, `name`, `overview`, `details` (array of
    paragraphs), and `diagnostics`.
2.  **Provisioning Files:** Create the `Makefile`, `.env.template`, and
    `docker-compose.yml` within the provider directory.
    Ensure the `Makefile`
    inherits from the root framework and defines `SERVICE_NAME`.
3.  **Distributed Networking:** In the `docker-compose.yml`, you must support
    multi-node routing.
    Do not hardcode internal Docker aliases if the target
    service might reside on another machine.
    Use the `.env.cluster` variables
    (e.g., `${ACTIVE_LOGGER_HOST:-active-logger}`) to allow dynamic fallback
    between the local bridge and the Tailscale mesh.
4.  **Priority Matrix Registration:** Update the routing matrix inside
    `./services/<plural_service>/.service.json` to evaluate and insert the
    new provider into the appropriate phase/OS priority permutations so the
    cluster orchestrator can deploy it.
5.  **Root Makefile Registration:** Ensure that the parent service's generic
    symlink (e.g., `$(SERVICES_DIR)/browser`) is present in the root `Makefile`
    under the `DOCKER_SUBDIRS` and `WIZARD_BOOT_ORDER` variables, and in the
    `-include` directives block. This ensures that global lifecycle targets like
    `make factory-reset-soft` or `make wizard` correctly teardown and boot the
    provider instead of leaving zombie containers running.
6.  **Documentation Generation:** Run `python bin/compile_md.py --setup` to
    generate the `index.md` documentation for the new provider.
7.  **Manifest Tracking:** Append all newly created files to
    `docs/MANIFEST.files`.
