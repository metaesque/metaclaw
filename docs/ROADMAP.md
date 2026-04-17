# OpenClaw Framework: Service Expansion Roadmap

This document outlines the prioritized architectural strategy for integrating
future software capabilities into the MetaClaw ecosystem. The phases are
structured by operational urgency: first securing the system, then granting it
capabilities, and finally scaling its autonomy.

*(Note: For the hardware scaling progression, please refer to the "Hardware
Journey" section in `ARCHITECTURE.md`)*

## Phase 1: Safe Execution (Sandboxing)

* **Urgency: CRITICAL.**

* **The Problem:** Currently, if the OpenClaw agent attempts to use a code
  execution tool to run Python or Bash scripts, it either crashes the gateway
  (due to missing Docker-out-of-Docker privileges) or runs with highly dangerous
  host-level access. We must establish a hardened execution perimeter
  immediately to prevent the agent from accidentally or maliciously corrupting
  the host OS.

* **Category:** `services/sandboxes/`

* **Target Providers:**
    * **gVisor / Firecracker:** For robust, local, hardware-level microVM
      isolation.
    * **E2B / Codeboxes:** For users willing to offload code execution to
      ephemeral, cloud-hosted environments.

## Phase 2: External Interaction (Browsers, Fetchers, and Searchers)

* **Urgency: HIGH.**

* **The Problem:** To perform meaningful real-world tasks, the agent needs the
  ability to visually interpret and interact with the modern web (browsing),
  bypass anti-bot measures to extract clean LLM-ready markdown (fetching), and
  execute high-speed queries to return structured snippets and real-time
  knowledge (searching) without conflating these distinct architectural vectors.

* **Categories:** `services/browsers/`, `services/fetchers/`,
  `services/searchers/`

* **Target Providers (Browsers):**
    * **Phase 0 Darwin (MacOS) host - Agent Browser:** MacOS runs Docker inside
      a lightweight VM, making host-networking and heavy Chromium instances
      incredibly resource-intensive for a 16GB laptop. Agent Browser is a native
      Rust-based CLI that bypasses Node.js bloat. Its sub-millisecond execution
      times and token-efficient "snapshot" accessibility trees mean you can run
      robust AI browser automation locally on a MacBook without spinning up its
      fans or exhausting unified memory.
    * **Phase 0 Windows host - Browser Use:** Windows handles Playwright
      exceptionally well via WSL2. Browser Use is Python-native, meaning it
      drops perfectly into OpenClaw's existing isolated `.venv`. It abstracts
      the heavy lifting of browser setup and provides highly reliable,
      multi-step execution right out of the box, making it the lowest-friction
      option for validating AI utility on a constrained Windows machine.
    * **Phase 1 Linux host - Stagehand:** A Phase 1 Monolith runs 24/7
      background tasks. Relying purely on vision-LLMs or dynamic DOM parsing for
      every single background scrape is financially ruinous. Stagehand allows
      OpenClaw to mix rigid deterministic code with AI. Once OpenClaw learns how
      to navigate a page, Stagehand caches those exact steps, bypassing the LLM
      entirely on subsequent runs. This drastically cuts API costs while
      maintaining the ability to "self-heal" if the website changes.
    * **Phase 3 Linux host - Skyvern:** Phase 3 nodes are dedicated "Blast
      Zones" built to handle heavy, volatile execution. Skyvern relies on
      computer vision and visual LLMs to literally "look" at the page, ignoring
      the HTML DOM entirely. This makes it impervious to anti-scraping
      obfuscation, but it requires massive CPU/RAM overhead to process
      screenshots and run local vision inference. A dedicated Phase 3 execution
      node is the only place this can run smoothly without bottlenecking your
      primary Gateway's routing latency.

* **Target Providers (Fetchers):**
    * **Phase 0 Darwin (MacOS) host - Jina AI Reader:** Running headless
      browsers inside Docker on macOS is exceptionally resource-intensive due to
      the virtualization layer. Jina AI Reader requires zero local
      infrastructure. It is a simple URL prefix (`https://r.jina.ai/`) that
      offloads all JavaScript rendering and markdown extraction to the cloud.
      This gives the local Mac agent robust fetching capabilities instantly
      without spinning up its fans or burning through the battery.
    * **Phase 0 Windows host - Crawl4AI:** Windows handles Python and Playwright
      exceptionally well locally via WSL2. Crawl4AI is entirely free,
      open-source, and extremely fast. It fits the Phase 0 "zero financial cost"
      ethos perfectly, giving the Windows user powerful, asynchronous scraping
      capabilities without needing a paid API key or relying on external cloud
      limits.
    * **Phase 1 Linux host - ScrapeGraphAI:** A Phase 1 Monolith runs 24/7
      background tasks. The biggest problem with automated scraping is that
      websites constantly update their CSS classes and HTML structures, which
      instantly breaks rigid scrapers. ScrapeGraphAI uses the node's local LLM
      runner to dynamically adapt and evaluate the page structure on the fly.
      This self-healing nature prevents your automated background fetches from
      breaking while you sleep.
    * **Phase 3 Linux host - Firecrawl:** Phase 3 nodes are dedicated "Blast
      Zones" built to handle heavy, concurrent execution. Firecrawl is an
      enterprise-grade platform that spins up multiple headless browsers,
      manages caching, and handles deep concurrent crawling via background
      workers. It requires significant infrastructure (Redis, PostgreSQL, worker
      nodes) that would crush a smaller Phase 1 machine, but it thrives on a
      Phase 3 node, turning it into a massive, private data-harvesting engine.

* **Target Providers (Searchers):**
    * **Phase 0 Darwin (MacOS) host - Tavily:** MacOS laptops running Docker
      often struggle with heavy internal virtualization overhead. Tavily
      requires absolutely zero local infrastructure. Unlike traditional search
      APIs that just return a list of URLs (forcing your local AI to
      individually fetch and read each one), Tavily is built for RAG. It
      actively synthesizes the answers on its own servers and returns a clean,
      factual summary. This drastically reduces the context window size and
      compute burden on your Mac's local LLM.
    * **Phase 0 Windows host - SearXNG:** Windows handles Docker efficiently via
      WSL2. SearXNG perfectly aligns with the Phase 0 "zero financial cost"
      ethos. It is a completely free, open-source metasearch engine that you
      host locally. By running SearXNG, your OpenClaw agent can scrape Google,
      Bing, DuckDuckGo, and Wikipedia simultaneously without ever needing a paid
      API key or worrying about corporate rate limits.
    * **Phase 1 Linux host - Exa:** A Phase 1 Monolith runs 24/7 background
      tasks, making token efficiency critical. Exa (formerly Metaphor) is a
      neural search engine that finds pages based on semantic meaning rather
      than exact keywords. More importantly, its "Highlights" feature extracts
      only the most highly relevant sentences from a webpage. By feeding
      OpenClaw just the highlights instead of the entire webpage DOM, you cut
      your local Ollama runner's token processing time by up to 50%.
    * **Phase 3 Linux host - Parallel AI Search:** Phase 3 nodes are dedicated
      execution environments meant to handle complex, multi-agent swarms doing
      deep research. Traditional search APIs force an agent to do multiple
      sequential searches (search -> read -> realize it needs more info ->
      search again), which creates endless, expensive loops. Parallel AI is
      engineered specifically for multi-hop reasoning. It can resolve complex,
      multifaceted queries by synthesizing scattered sources in a single pass,
      drastically reducing the latency and cost of long-running enterprise
      research tasks.

## Phase 3: Source Truth & Reliability (VCS & CI)

* **Urgency: MEDIUM.**

* **The Problem:** As agents begin generating complex code and autonomously
  modifying workspace files, we need absolute attribution (knowing exactly who
  changed what, and when) and automated testing to ensure the AI's generated
  artifacts don't break existing systems.

* **Category:** `services/vcs/` & `services/ci/`

* **Target Providers:**
    * **Forgejo / Gitea:** Lightweight, self-hosted version control to track
      all agent modifications locally.
    * **Woodpecker CI / Drone:** Lightweight CI runners that integrate tightly
      with local VCS to mathematically prove the agent's code works before
      deployment.

## Phase 4: Decoupling & Debugging (Queues & Tracing)

* **Urgency: MEDIUM.**

* **The Problem:** As multi-agent workflows become more complex, relying on
  synchronous HTTP calls between the Gateway and the Proxy will result in
  timeouts and severe bottlenecking. We must decouple the architecture to
  support asynchronous workloads and gain deep visibility into latency spans to
  figure out *why* an agent is slow.

* **Category:** `services/queues/` & `services/tracers/`

* **Target Providers:**
    * **RabbitMQ / NATS:** For asynchronous task brokering and queuing.
    * **OpenTelemetry + Jaeger / SigNoz:** For visualizing multi-hop execution
      spans across the proxy and inference models.

## Phase 5: Secure Public Ingress (Reverse Proxy & IAM)

* **Urgency: LOW (Deferred).**

* **The Problem:** While Tailscale handles secure remote administration for the
  system owner, exposing specific agent endpoints (like a shared chatbot or a
  public webhook receiver) to external users requires a strict public-facing
  security perimeter.

* **Categories:** `services/proxies-reverse/`, `services/iam/`

* **Target Providers:**
    * **Traefik / Caddy:** For automated SSL termination and external request
      routing from the open internet.
    * **Authelia / Authentik:** To enforce stringent Multi-Factor Authentication
      (MFA) and Single Sign-On policies before granting public access to any
      exposed services.
