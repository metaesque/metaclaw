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
vulnerability. Meta<Claw> relies on an overlay mesh network (like Tailscale) for
secure, zero-trust access.

1. Install Tailscale on all your homebase nodes and your travel laptop.

2. Note the static `100.x.y.z` IP assigned to your Tier 1 Monolith (the Control
   Plane).

3. Open your browser and navigate to `http://[Tailscale-IP]:18789` to access
   the OpenClaw Dashboard securely from anywhere.

4. To run `make` commands remotely, SSH into the node using its mesh IP:
   `ssh user@[Tailscale-IP]`.

### Core Development Workflow (Headless)

MetaClaw is designed for headless deployment. Active development of the
framework should occur directly on the cluster nodes over SSH, not via local
file transfers.

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

## Testing Semantic Routing (Vector Space)

When editing agent personas or expanding the workspace, you must ensure that
your new agents do not cause "semantic bleed" (where two agents have overlapping
skill descriptions, confusing the mathematical router).

1.  **Regenerate Utterances:** After editing a `workspace/agents/**/*.yaml`
    file, run `make patch` from the repository root. This script will
    automatically extract your new `skill_signature` strings and compile them
    into `services/proxies/litellm/utterances-agents.yaml`.

2.  **Compile the Router:** Navigate to `services/proxies/litellm/` and run
    `python advanced/generate_router.py -k agents`. This loads the utterances
    into the active `router.json` payload.

3.  **Visual Verification:** Run `python advanced/plot_clusters.py` to generate
    a `semantic_clusters.png` file. Download this file to your local machine and
    verify that your agent clusters are mathematically distinct (not
    overlapping).

4.  **Test Thresholds:** Run `python advanced/test_thresholds.py` to simulate
    a dozen sample prompts against your active LiteLLM proxy and verify they
    match the intended domain agent with a confidence score > 0.70.

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

If you are on the `main` branch, have pushed broken commits, and want to
violently rewind the branch to the stable point (throwing away all commits made
after the tag):

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

### The "Soft Reset" & Cluster Bring-Up Sequence (Recommended)

This is the standard troubleshooting step. It cleanly shuts down all containers,
deletes the internal network, and scrubs ephemeral runtime files. **Crucially,
it preserves your API keys, your PostgreSQL database, and your Python
environments.** To properly tear down and rebuild your cluster, always follow
this strict sequence:

1.  In your terminal, run: `make factory-reset-soft` to clear old state
    gracefully.

2.  Run `make setup`: Re-profiles your local hardware and assigns architectural
    planes. *Note: This command is now executed once from the Control node. It
    profiles the entire cluster and automatically broadcasts the configuration
    to all remote hosts.*

3.  Execute the deployment wizard. Choose one of the following based on your needs:

    *   `make wizard-cluster`: The new default for multi-node setups. It
        orchestrates the deployment sequence across the entire distributed
        cluster automatically via SSH.

    *   `make wizard-batch`: A non-interactive deployment sequence for a
        single node. Bypasses all human-in-the-loop prompts assuming `.env.json`
        secrets are intact.

    *   `make wizard`: The interactive deployment sequence. Pulls up a helpful
        Chrome browser with service/provider-specific information and diagnostic
        checks as setup occurs.

4.  Run `make gui`: Opens the OpenClaw interface with your secure access token.

### The "Nuclear Option" (Hard Reset)

Use this only if you need to completely purge everything, including your
database records, vector embeddings, and stored API keys.

1.  In your terminal, run: `make factory-reset-hard`

2.  Run `make setup` to re-profile your hardware from scratch across the
    cluster.

3.  You will need to run `make wizard-cluster` (or `make wizard`) and re-enter
    all your API credentials as if you were installing the framework for the
    first time.

## Troubleshooting Telemetry & Dashboards

If your Grafana hardware dashboards are missing data or displaying incorrect,
overlapping anomalies, consult the following diagnostic paths.

### 1. Duplicate Lines in Grafana Legends
If you observe duplicate legend entries (e.g., 2 compute devices, 2 routers) in
the "Power Draw per Device" panel, it means multiple nodes in your cluster are
simultaneously successfully completing UDP broadcast discoveries.
*   **The Fix:** Ensure your PromQL query uses the `max by (device)` aggregation
    to automatically collapse duplicated metrics into a single logical line (e.g., `max by (device) (kasa_power_watts)`).

### 2. Utilizing the Services API (Python)
MetaClaw provides a programmatic abstraction layer for system introspection. If
you need to verify if the Telegraf collector or the logging daemon is running
programmatically (e.g., inside an agent's sandbox script), you can utilize the
Services API:
```python
import sys
sys.path.insert(0, '/metaclaw/lib')
from services import Collector, Forwarder

telegraf = Collector("telegraf")
print(telegraf.status()) # Output: running
print(telegraf.log(tail=5))
```

## Troubleshooting Local GPU Inference (Ollama)

Running large models on edge hardware (like AMD APUs) often encounters
proprietary driver bottlenecks. If your Ollama log
(`services/runners/ollama/ollama.log`) reports `library=cpu` and massive token
latencies, follow this diagnostic path:

1. **Verify OS Kernel Support:**
   Run `uname -r`. If you are running an LTS kernel (e.g., 6.8) but possess
   bleeding-edge silicon (like RDNA 3.5), the OS will not detect the GPU.
   Install the HWE stack to upgrade to Linux 7.0+: `sudo apt install
   linux-generic-hwe-24.04` and reboot.

2. **Verify Hardware Enumeration:**
   Run `rocm-smi`. You must see your discrete GPU or APU listed in the table. If
   you see `WARNING: No AMD GPUs specified`, your kernel upgrade failed or
   driver packages are missing.

3. **Bypass ROCm Restrictions (APUs Only):**
   Integrated graphics often fail Ollama's proprietary ROCm CGo compilation
   checks. If the OS sees the GPU but Ollama doesn't, force the Vulkan compute
   API. Ensure `OLLAMA_VULKAN=1` and `OLLAMA_IGPU_ENABLE=1` are exported in the
   environment. **Never use `HIP_VISIBLE_DEVICES=-1`**, as this blinds the
   hardware scanner entirely. If you are hitting AMD SVM limits (swap
   thrashing), you may also need to set `ROCR_VISIBLE_DEVICES=none` to prevent
   ROCm from locking system memory.

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

4.  **Rebuild:** Run `make factory-reset-soft` followed by `make wizard-batch`
    to cleanly instantiate the new version.

## Validating the Routing Engine (Cost Control)

To save money, Meta<Claw> uses a "Predictive Router" that sends trivial
questions to cheap models and complex tasks to expensive ones. If responses feel
sluggish, or your API bill suddenly spikes, this router might be broken.

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

### Testing Agent Specific Prompts

You can also bypass the Web GUI entirely and test specific agents and
complexities using the testing script. If you add a `tests:` array block to an
agent's YAML file containing custom prompts, you can execute them directly:

```bash
# Tests the 'simple-model' prompt explicitly defined in the pm.yaml file
python bin/openclaw_test.py -t simple -a openclaw/software_pm
```

## Verifying Internal DNS (Aliases)

When building providers that act as primary backends (e.g., `active-browser`,
`active-fetcher`), you must verify that the internal Docker DNS aliases are
successfully registered.

Do NOT use `docker network inspect <network_name>` for this. The Docker daemon
does not expose container-level aliases in the network's root `Containers` map;
it only lists the primary container name and its assigned IP address.

To accurately verify an alias, you must inspect the container's isolated network
settings:

1. Execute a targeted inspection:
   `docker inspect <container_name> --format '{{json .NetworkSettings.Networks}}'`

2. Alternatively, simply grep the raw configuration:
   `docker inspect <container_name> | grep active-`

If the alias is missing, verify that your `docker-compose.yml` nests the
`aliases` array correctly beneath the specific network attachment block.

## Managing the Graphical User Interface (GUI)

The OpenClaw Web UI access has been streamlined to bypass manual pairing.

* **Authentication:** A secure token is automatically injected into the
  gateway via the `OPENCLAW_GATEWAY_TOKEN` environment variable (defaulting to
  your `ACTIVE_PROXY_KEY`).

* **Launch:** Running `make gui` from the framework root will instantly
  launch the dashboard in your native browser using the injected token.

* **First Run:** Running `make wizard` handles this sequence
  automatically, opening the GUI once the backend is healthy and fully
  configured.

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

## Services

MetaClaw abstracts its infrastructure into mutually exclusive "services." Only
one provider for a given service runs at a time on any particular node.

### Execution Sandbox (`sandboxes`)

#### Hardened Docker DooD

The `docker-dood` provider offers a persistent, isolated Python execution
environment for agent workflows.

- **CLI Interaction:** You can manually test commands inside the sandbox by
  running `docker exec -it docker-dood-sandbox /bin/sh`.

- **Configuration:** The container automatically attempts to install any Python
  dependencies defined in your workspace at `workspace/src/requirements.txt`
  upon startup.

### Secrets Manager (`secrets`)

### Overlay Network (`networks`)

#### Tailscale

Tailscale is the default zero-configuration mesh VPN.

- **CLI Interaction:** To view your active cluster nodes and their assigned
  `100.x.y.z` IP addresses, run `tailscale status` on your host machine.

- **Exposing Webhooks:** To securely expose a local port (like 18789) to the
  public internet for incoming webhooks, use the Funnel feature: `tailscale
  serve --bg <port>`.

### Identity & Access Management (`iam`)

### Log Aggregator (`loggers`)

#### VictoriaLogs

VictoriaLogs is the ultra-lightweight full-text log search engine.

- **UI Interaction:** Navigate to `http://[Your-Tailscale-IP]:9428/select/vmui`
  to access the visual querying interface.

- **API Interaction:** You can query the database for raw log lines directly via
  the LogsQL API:
  `curl -s "http://localhost:9428/select/logsql/query?query=_stream_id:*"`

### Telemetry Forwarder (`forwarders`)

#### Fluent Bit

Fluent Bit is a background edge daemon that tails local logs and forwards them
to VictoriaLogs.

- **Configuration:** Modify `services/forwarders/fluentbit/fluent-bit.conf`
  to add new log file paths or container filters.

- **CLI Testing:** To verify log ingestion locally, tail the active container
  output: `docker logs -f fluentbit-forwarder`

### Distributed Tracer (`tracers`)

### Time-Series Database (`tsdbs`)

#### VictoriaMetrics

VictoriaMetrics runs as the backend storage engine for numerical time-series
metrics.

- **UI Interaction:** Navigate to `http://[Your-Tailscale-IP]:8428/select/vmui`
  in your browser to access the `vmui` interface for writing PromQL/MetricsQL
  queries directly against the database.

- **API Interaction:** You can query the database for raw JSON metrics directly
  using `curl` from your terminal:
  `curl -s "http://localhost:8428/api/v1/query?query=system_uptime"`

### Metrics Collector (`collectors`)

#### Telegraf

Telegraf is a background daemon that scrapes metrics from the host machine (or
executes custom Python scripts) and pushes them upstream to VictoriaMetrics.

- **Configuration:** Modify `services/collectors/telegraf/telegraf.conf` to add
  new inputs, such as executing custom Python hardware scrapers via
  `[[inputs.exec]]`.

- **CLI Testing:** To test if Telegraf is correctly parsing your custom script's
  output without pushing junk data into the live database, you can force it to
  run a single test collection and print to standard output:
  `docker exec telegraf-collector telegraf --config /etc/telegraf/telegraf.conf --test`

### Data Visualizer (`visualizers`)

#### Grafana

Grafana provides human-readable dashboards, graphs, and alerts for your
observability stack.

- **UI Interaction:** Navigate to `http://[Your-Tailscale-IP]:3000/` and log in
  with your configured admin credentials (defined during `make setup`).

- **Setup:** To visualize your metrics, add a new "Prometheus" datasource
  pointing to the internal Docker network URL `http://active-tsdb:8428`. You can
  then create panels and write PromQL queries to build your dashboards.

### Web Fetcher (`fetchers`)

#### Crawl4AI

Crawl4AI is an ultra-fast web crawler designed specifically for LLMs, extracting
clean Markdown natively.

- **API Interaction:** Crawl4AI exposes a REST API on port `11235`. You can
  verify its health via `curl -s http://localhost:11235/health`.

- **Usage:** Agents interact with it programmatically to fetch and parse
  websites. If deployed securely, remember to pass the `CRAWL4AI_API_TOKEN` in
  the Authorization header.

### Web Search API (`searchers`)

#### SearXNG

SearXNG is a privacy-respecting metasearch engine that aggregates results from
dozens of search engines.

- **UI Interaction:** You can perform manual searches by navigating your
  browser to `http://[Your-Tailscale-IP]:9003/`.

- **API Interaction:** Agents query the `/search?q=...&format=json` endpoint
  on port `9003` to retrieve structured search snippets.

### Browser Automation (`browsers`)

#### Browser Use

Browser Use is an API that allows agents to autonomously control web browsers
using natural language.

- **API Interaction:** The REST API listens on port `8080`. Agents POST task
  payloads to `http://localhost:8080/tasks`.

- **UI Interaction (VNC):** You can visually watch the agent interact with the
  web page in real-time by opening `http://[Your-Tailscale-IP]:8080/vnc.html` in
  your browser.

### LLM Runner (`runners`)

#### Ollama

Ollama is the local inference engine that runs GGUF models directly on
bare-metal hardware.

- **API Interaction:** Ollama listens on port `11434`. You can list loaded
  models via `curl -s http://localhost:11434/api/tags` or generate text via the
  `/api/generate` endpoint.

- **CLI Interaction:** From the Compute Node, you can manually interact with
  models by executing `./bin/ollama run <model_name>` within the
  `services/runners/ollama/` directory.

### Continuous Integration (`ci`)

### Message Queue (`queues`)

### Event Gateway (`events`)

### Ingress (`ingresses`)

### AI Gateway (`gateways`)

#### OpenClaw

OpenClaw is the primary agentic framework and multi-modal gateway.

- **UI Interaction:** Access the primary web dashboard at
  `http://[Your-Tailscale-IP]:18789`.

- **CLI Interaction:** For direct terminal access to the agent streams,
  execute: `docker exec -it openclaw-gateway openclaw tui`

### AI Proxy (`proxies`)

#### LiteLLM

LiteLLM is the centralized proxy layer that routes traffic and calculates token
costs.

- **API Interaction:** Ensure models are loaded and available by querying
  `curl -s -H "Authorization: Bearer $ACTIVE_PROXY_KEY" http://localhost:4000/v1/models`.

- **CLI Testing:** To verify the routing logic is correctly passing payloads to
  your chosen provider, run the diagnostic testing script:
  `python bin/litellm_test.py -t complex`.

### Version Control System (`vcses`)

### Long-Term Memory (`memories`)

#### PostgreSQL + pgvector

PostgreSQL manages both the structured operational state of the cluster and the
high-dimensional embedding vectors for agent semantic recall.

- **CLI Interaction:** You can launch a Postgres shell directly into the primary
  database: `docker exec -it postgres-memory psql -U postgres -d openclaw_db`

- **External Tooling:** The database is exposed locally on port `5432`. You can
  connect external GUI tools (like DBeaver or pgAdmin) using the connection
  string defined in your `services/memories/postgres/.env` file.

### Real-Time Cache (`caches`)

#### Redis

Redis serves as the ultra-low latency key-value store for ephemeral session
state, rate limiting, and pub/sub agent communication.

- **CLI Interaction:** You can interact with the Redis cache natively from
  your host terminal using the Docker exec command:
  `docker exec -it redis-cache redis-cli`

- **Commands:** Once inside the CLI, you can verify connectivity (`PING`) or
  inspect the current keyspace (`KEYS *`).
