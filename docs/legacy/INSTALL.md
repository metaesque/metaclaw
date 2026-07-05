# Intro

The plethora of "How to install OpenClaw" videos on youtube tends to provide
only a surface-level treatment of many important topics. This document provides
a hierarchically organized exploration of all the concepts (both within OpenClaw
and in the broader ecosystem within which OpenClaw operates) that you need in
order to start interacting with OpenClaw.

Here are the core topics we need to explore:

1. **AI Models**: Decide what AI models (Gemini, Claude, OpenRouter, etc)
   we are going to use (many options!)

2. **Security thru Containment (Docker)**: Explains what Docker does, why
   it helps with security and maintenance, and how to install it.

3. **AI Proxy**: Allows OpenClaw to interact with your AI models (by running
   an AI Proxy like LiteLLM in a Docker image)

4. **Installing OpenClaw**: Get OpenClaw running in Docker

5. **Setting Up Channels**: Establish how you are going to communicate with
   OpenClaw (many options!)

6. **Browser**: Give OpenClaw the ability to search the web

7. **Local Models**: Establish how to control local models (NOT in Docker)


## Sibling Technologies

- Gateway
   - purpose: personal AI agent
   - options:NanoClaw, Moltis, TrustClaw, ZeroClaw, Nanobot, PicoClaw, NullClaw, Manis AI, Knolli AI, Claude Code, n8n + AI
- AI Proxy
   - purpose: middleware between OC and LLMs (control plane for cost, safety and model flexibility)
   - options: LiteLLM, OpenRouter, Manifest, Bifrost, Helicone, Portkey, TrueFoundry)
   - research: https://gemini.google.com/u/1/app/66fa255ddd9cf417
- LLM Runner
   - purpose: manage and execute local LLMs on baremetal
   - options: vLLM, llama.cpp, Ollama, LM Studio, LocalAI, KoboldCPP, Text-Gen-WebUI, Jan.ai, Msty, GPT4All
   - research: https://gemini.google.com/u/1/app/fd65e9f147b28daa
- Memory (Long-term)
   - purpose: maintain effective space-efficient long-term memory of agents
   - options: !SqLite, PostgreSQL+pgvector, Qdrant, Milvus, Weaviate
- Cache (Real-time memory)
   - purpose: semantic caching (in LiteLLM), rate limiting & quotas (in LiteLLM), multi-agent pub/sub, distributed locking
   - options: !Memcached, Redis, Turso, Convex, Memori Labs, Context Lakes, Milvus
- Log Aggregation
   - purpose: provide the visibility needed to monitor agent behavior, troubleshoot tool execution errors, and ensure security when the agent is given full system access.
   - options: Promtail/Loki, Filebeat/Elk
- Message Queue
   - purpose: decouples the Gateway from the execution nodes. Instead of synchronous HTTP calls, the Gateway pushes tasks to a queue. Worker nodes consume tasks at their own pace. This prevents the Gateway from timing out if a model takes 60 seconds to generate a response.
   - options: OC builtin?, RabbitMQ, NATS, Kafka
- Tracing
   - purpose: standard logging (Loki,Elk) tells you _what_ happened. Tracing tells you _how_ long a specific agent's thought process took across the Gateway, LiteLLM, and Postgres. Essential for debugging latency in multi-step agent trajectories.
   - options: OpenTelemetry Collector + Jaeger, ???
- Sandboxing
   - purpose: If your agents are writing and executing Python or bash scripts (Code Interpreter capabilities), you cannot run that code directly on the host OS. Docker alone is insufficient security against a malicious or hallucinated script.
   - options: !Docker, gVisor, Firecracker microVMs
- Reverse Proxy
   - purpose: SSL termination, load balancing incoming API requests, and rate limiting (must co-locate with Gateway, acts as front door)
   - options: Traefix, HAProxy
- Version Control Systems
   - purpose: track every file change in a space efficient manner, provide agent attribution for every file modification
   - options: GitHub, GitLab, Bitbucket, Gitea, Codeberg, Forgejo, Gogs, SourceHut, OneDev
- Continuous Integration (CI):
   - purpose: supports frequent merging of code changes into a central repository, triggering automated builds and tests.
   - options: GitHub Actions, GitLab CI/CD, BitBucket Pipelines, Gitea/Drone, Buildkite, Jenkins
- Browser Automation
   - purpose: give OC the ability to search the web and obtain structured data from those searches
   - options: Chromium/Browser tool, Firecrawl Browser Sandbox, Browser Use, Stagehand, Agent Browser, ScrapeGraphAI, Crawl4AI, Zyte, Puppeteer, Playwright, Selenium, Octoparse, Browse AI, SearXNG
- Docker
   - purpose: service/resource containment on hardware
   - options: Docker Destkop, Podman Desktop, Rancher Desktop, Orbstack, Portainer, LXD/LXC
- Channels
   - purpose: how person communicates with OC
   - options: TUI, web GUI, Telegram, Discord, Google Chat, Whatsapp, Slack, ...

# Brains (aka AI Models)

AI models provide the actual "brain" for OpenClaw. Whenever you ask OpenClaw a
question or give it a task, the system must consult an artificial intelligence
model to figure out what the text means and what words should come next.

Think of this as the engine of a car. OpenClaw provides the steering wheel and
the dashboard, but it relies on the engine to provide the actual horsepower.
Without AI models, OpenClaw wouldn't be able to "think" or make decisions about
which tools to use.

**Terminology:** Local LLM Runner, Inference Engine, Model Provider.

## Categories

The subsections below cover all the different ways you can run these AI brains
Because there are so many ways to host an AI, they have been grouped into
categories based on how they are built and where they run. Some are designed for
massive enterprise servers, while others are built to run efficiently on an
everyday laptop.

### Category 1: LLM Inference Engines / Runners

This category represents LLM Runners (aka LLM inference engines), which allow
you to run AI models locally on your own hardware. The size and capability
of the AI models that can be run depend on how powerful the hardware is:

* **Small**: Normal laptops/desktops can only run the smallest AI models (<7B-10B parameters) locally
* **Medium**: Large computers (32GB RAM, GPUs + VRAM) are needed to run medium AI models (10B-70B)
* **Large**: Powerful computers (96-128GB RAM, 96GB+ VRAM) are needed to run powerful AI models (70-120B), and use production-quality LLM runners
* **Huge**: Custom computers (128GB-256GB RAM, 120GB+ VRAM) are needed to run the largest AI models (120B-1T+), and use production-quality LLM runners

Note that not all AI models are "open" (available to be run on local hardware).
For example, all Anthropic Claude models are proprietary, closed source models
that live on Anthropic's servers. Google provides its Gemma family of AI models
for local use, but does not allow its Gemini family to be run locally. Most AI
providers make some models open, and keep some closed.

This category can be further divided into CLIs, GUIs, and Enterprise Frameworks

#### Bare-Metal CLI Inference Daemons

You interact with these LLM runners via command line interfaces.

**Examples:** Ollama, Llama.cpp (Server mode), ExLlamaV2.

Important considerations in this sub-category:

* **Weight Serialization & Quantization Formatting:** Before an AI can think, it has to be loaded from your hard drive into your computer's active memory. This process involves reading highly compressed files that contain the AI's "knowledge." By carefully controlling how this information is unpacked, the system ensures the AI doesn't use up all of your computer's available memory.

* **Compute Graph Compilation:** Once the data is loaded, the software has to figure out exactly how to run the AI's complex math on your specific computer. It translates the AI's internal structure into a step-by-step blueprint that your processor can actually understand and execute.

* **Context & KV Cache Allocation:** As you chat with the AI, it needs to remember what was said a few minutes ago. This step involves reserving a specific chunk of your computer's memory to act as the AI's short-term scratchpad, holding onto the conversation history.

* **Network Listener & Concurrency Queue:** Finally, this software sets up a small, invisible "listening post" on your computer. It constantly waits for OpenClaw to send it a new question or task, organizing requests into a neat line so the AI handles them one by one.

#### Desktop GUI & Managed Local Wrappers

You interact with these LLM runners via graphical user interfaces.

**Examples:** LM Studio, Jan, GPT4All, Msty.

Important considerations in this sub-category:

* **Model Registry & Discovery:** For users who prefer a point-and-click experience over typing code, these tools provide a visual storefront. You can easily search for, filter, and download new AI brains with the click of a button.

* **Runtime Parameter Abstraction:** These tools provide a clean, user-friendly settings menu. Instead of forcing you to type complex technical commands to adjust how the AI thinks, you can simply adjust sliders and checkboxes.

* **Headless Engine Orchestration:** Behind the scenes, these visual tools invisibly manage the complicated, code-heavy engines mentioned in Category 1, turning them on and off automatically so you don't have to.

* **OpenAI API Bridge:** These wrappers trick OpenClaw into thinking it is talking to a standard, internet-based AI service, seamlessly translating standard internet requests into commands your local computer can process.

#### High-Throughput Enterprise Serving Frameworks

These are all high-performance LLM runners designed to optimize the serving of
large language models in production environments. They are primarily CLIs or
libraries/frameworks.

**Examples:** vLLM, Text Generation Inference (TGI), TensorRT-LLM, SGLang.

Important considerations in this sub-category:

* **Continuous Batching Scheduler:** Designed for massive servers handling
  thousands of users, this system groups pieces of different conversations
  together instantly to ensure the expensive server hardware is never sitting
  idle for even a fraction of a second.

* **Paged KV Cache Memory Manager:** A highly advanced way of organizing the
  server's memory, similar to how modern operating systems work, preventing
  memory fragmentation and allowing the server to handle incredibly long
  documents.

* **Tensor Parallelism Router:** When an AI brain is simply too massive to
  fit on a single computer chip, this logic splits the AI's knowledge across
  multiple different chips, stitching their answers back together at lightning
  speed.

* **Optimized Attention Kernels:** Highly specialized bits of code written
  specifically for top-tier enterprise hardware to ensure the AI pays attention
  to the right words as quickly as physically possible.

### Category 2: Managed Proprietary Cloud APIs

These are Enterprise LLM Platforms or AI Providers (not LLM runners). They are
cloud-based API services that let developers and companies use advanced,
proprietary Large Language Models (LLMs) without managing hardware. They provide
access to models, like GPT-5, Claude 4.6 Opus, Gemini 3.5 Pro, and Cohere
Command R. They also offer playground environments for prompt testing, API
documentation, fine-tuning tools, and safety measures

**Examples:** OpenAI Platform, Anthropic Console, Google AI Studio, Cohere.

Important considerations in this category:

* **Managed Inference**: They handle the computing power needed to run the
  models.

* **API Gateway & Quota Enforcement:** These are the digital toll booths of the
  internet's biggest AI providers. They check your password, count how many
  words you are sending, and ensure you are billed correctly for the service.

* **Safety & Alignment Filter:** Before answering, these companies pass your
  request through strict safety filters to ensure the AI does not say anything
  dangerous, illegal, or against their corporate policies.

* **Data Security & Compliance**: They offer enterprise-grade privacy to
  ensure user data isn't used for model training.

* **Proprietary Foundation Model:** The highly secretive, incredibly powerful
  AI brains developed by these tech giants. You cannot download these; you can
  only rent access to them over the internet.

* **Hyperscaler Autoscaling:** An invisible system that automatically turns on
  hundreds of new servers in a remote warehouse if millions of people suddenly
  decide to use the AI at the same time.

### Category 3: Hardware-Accelerated Open-Weight APIs

This category is for specialized AI inference providers (or AI infrastructure
companies) rather than traditional LLM "runners". They are designed specifically
to run pre-trained Large Language Models (LLMs) with extremely low latency and
high throughput, largely outperforming general-purpose GPU cloud providers for
inference tasks.

**Examples:** Groq, Cerebras, Together AI, Fireworks AI.

* **Groq**: Focuses on unparalleled, low-latency speed using custom Language
  Processing Units (LPUs), ideal for real-time conversational AI.

* **Cerebras**: Offers high-throughput inference utilizing massive wafer-scale
  chips, excelling at high-volume, batch-processing tasks.

* **Together AI**: Specializes in running open-source models with high speed,
  reliability, and scalability for developers.

* **Fireworks AI**: Optimized for low-latency, multimodal open-source model
  serving with specialized CUDA kernels.

They differ from traditional "LLM Runners" in:

* **Hardware Specialization**: Groq and Cerebras use custom, purpose-built
  hardware, whereas traditional runners often rely on general-purpose Nvidia
  GPUs.

* **Inference-Only Optimization**: These platforms are optimized specifically
  for fast generation (throughput), not for training, allowing them to provide
  higher performance.

* **Speculative Decoding Engine:** A clever trick where a tiny, fast AI
  guesses the next few words, and a bigger, smarter AI simply double-checks the
  work. This massively speeds up how quickly text appears on your screen.

* **API-First Approach**: They provide optimized API endpoints for open-source
  models (Llama, Mixtral) designed to act as high-speed alternatives to closed
  APIs like OpenAI.

* **API Normalization Interface:** A layer that takes these experimental,
  ultra-fast chips and makes them look like standard AI connections, so OpenClaw
  can plug into them without needing special software.

Together AI and Fireworks AI primarily use specialized GPU clusters, while Groq
and Cerebras utilize proprietary hardware accelerators

### Category 4: Serverless & Ephemeral Model Hosting

These are cloud-based, fully managed services that provide the infrastructure
(GPUs, Kubernetes clusters, etc.), automatic scaling (including scaling to zero
when idle), and API endpoints for serving LLMs. Users pay for the compute time
used, and do not need to manage the underlying machine configurations.

**Examples:** Replicate, RunPod Serverless, Hugging Face Inference Endpoints,
AWS SageMaker Serverless.

These platforms abstract away the complexity of infrastructure management (e.g.,
provisioning GPUs, managing servers, setting up scaling, handling API
endpoints). Users can deploy their models (often by simply providing a link to a
model on Hugging Face Hub) and are charged based on usage (pay-per-second, or
per inference request). They leverage various optimized "runners" like vLLM
internally for high-throughput and memory efficiency.

Important considerations in this category:

* **Container Lifecycle Orchestrator:** This system allows you to rent a
  powerful computer only for the exact seconds you need it. When you send a
  message, it wakes a sleeping server up, runs your AI, and then immediately
  shuts it down so you stop paying.

* **Weight Caching & Storage Network:** Because waking a server up from sleep
  takes time, these systems use massive, ultra-fast hard drives to load
  gigabytes of AI data into memory in mere seconds.

* **Custom Endpoint Router:** A dedicated web address created just for you,
  ensuring your OpenClaw system always knows exactly where to send its requests
  in the cloud.

## API Keys

If you aren't running every model on local hardware (unlikely, unless you have
very impressive hardware), you will eventually need to create something called
an API key (and you'll probably create multiple such keys). Think of an API key
as a metaphorical key that gives you access to AI-related resources and AI
models on a specific AI Provider's infrastructure. Each key is associated with a
billing/payment method (so the provider can charge you) and spend limits (so you
can control how much OpenClaw consumes when using that API key).

A crucial aspect of setting up OpenClaw is indicating which API keys to use for
which agents, and storing those API keys securely (since anyone with those keys
can use them the same way you can).

# Security & Containment (Docker)

OpenClaw is not just a chatbot that responds to prompts, it can *do* things in
its environment (exactly what it can do is up to you to configure). Putting
bounds on what OpenClaw (more accurately, bounds on what each agent within
OpenClaw) can do is all part of the security aspect of OpenClaw that must be
treated as a priority during installation.

Security operates at many different levels. This section is about hardware-level
security, but wrapping OpenClaw (and related technologies) in protective
bubbles. The technology used for this is called Docker.

## Introduction to Docker for OpenClaw

**Analogy #1: The Pop-up Magical Kitchen**

Imagine you are trying to bake a very specific cake (OpenClaw), but it requires
a very specific oven, a certain brand of flour, and exactly 50% humidity in the
kitchen. If you try to bake it in your normal kitchen, you might have to
rearrange everything, buy new tools, and risk ruining your regular meals.

Docker is like having a pop-up, magical kitchen that appears inside your house.
It comes pre-stocked with the exact oven, ingredients, and environment the cake
needs. When you are done baking, the pop-up kitchen disappears, leaving your
real house completely untouched.

In technical terms, Docker creates isolated "containers" (the magical kitchens)
where software can run perfectly, separated from the rest of your computer's
files and settings.

**Analogy #2: Cargo Shipping Containers**

Think of your computer as a cargo ship and the software you want to run as the
cargo. Before shipping containers were invented and standardized, one had to
figure out how to pack loose grain, fragile glassware, and heavy machinery into
the same hull without them destroying each other. When shipping containers
arrived, it was much easier to fill ships to capacity without damaging or mixing
up the cargo.

Docker introduces the software equivalent of the standardized shipping
container. It allows developers to pack an application (like OpenClaw) along
with everything it needs to function — its specific files, libraries, and
background tools — into a single, sealed digital box. This container can be
dropped onto any computer, and it will run exactly the same way without
interfering with the rest of your system. The container is tied into the local
infrastructure (it uses the CPU, RAM, disk, etc. of the computer), but the user
can place strict limits on how much and which resources the container uses.

## OpenClaw in Docker?

### Pros

Installing complex software like OpenClaw directly onto your personal laptop can
be risky and messy. Here is why wrapping it in a Docker image is the superior
approach:

* **Zero "Dependency Hell":** OpenClaw likely requires very specific versions of coding languages (like Python) or background libraries. Installing these directly can break other software on your laptop. Docker keeps OpenClaw's requirements locked inside the container.
* **Easy Cleanup:** If you decide you do not want OpenClaw anymore, you simply delete the container. If you install it directly, it scatters files and settings deep into your operating system, which are difficult to fully remove.
* **Security and Isolation:** A Docker container is a sandbox. If something goes wrong with OpenClaw, it is trapped inside the container and cannot easily damage your laptop's core operating system.
* **Guaranteed to Work:** "It works on my machine" is a common developer excuse. Because Docker containers include the exact environment the developer used to build the app, it will run exactly as intended on your machine, regardless of your setup.

### Cons

While containerization offers environment consistency, it introduces specific system-level penalties that may make a bare-metal or standard virtual machine deployment preferable for OpenClaw, depending on its specific workload requirements.

* **I/O and Filesystem Overhead**: On non-Linux host operating systems (macOS
  and Windows), Docker relies on a lightweight utility VM. Volume mounting
  across the OS boundary introduces significant filesystem latency. If OpenClaw
  executes high-frequency read/write operations on large datasets, this
  virtualization overhead will severely bottleneck performance.

* **Hardware Abstraction and Pass-through**: If OpenClaw requires direct access
  to specialized hardware, such as serial ports, USB controllers, or raw GPU
  compute, Docker complicates the architecture. While technologies like the
  NVIDIA Container Toolkit exist, configuring direct hardware pass-through adds
  fragility and operational overhead compared to a native installation.

* **Network Latency and Complexity**: By default, Docker bridges container
  networking through a virtual interface, introducing NAT overhead. For
  applications demanding ultra-low latency or relying on complex
  broadcast/multicast protocols, managing host networking or configuring macvlan
  networks inside Docker increases architectural complexity and the surface area
  for routing failures.

* **State Management and Data Persistence**: Containers are ephemeral by design.
  If OpenClaw is heavily stateful and requires complex database management,
  handling volume persistence, backup, and restoration processes through Docker
  adds an unnecessary layer of indirection. A native system service interacting
  directly with block storage is often more robust for critical stateful
  workloads.

* **Security Privilege Escalation Risks**: The standard Docker daemon runs with
  root privileges. Mounting host directories or sockets into the OpenClaw
  container creates a vector for privilege escalation if the container is
  compromised. While rootless modes exist, they often introduce further
  networking and permission constraints that can break application
  functionality.

* **Debugging and Observability Friction**: Tracing system calls, attaching
  native debuggers, or profiling memory leaks within a containerized environment
  requires elevated privileges and specific tooling configurations. Running
  OpenClaw natively allows for immediate, unhindered access to standard system
  profiling tools.

## Installation Guides by Operating System

### macOS

* **Docker Desktop:** The standard, all-in-one solution. Download the `.dmg` file from the official Docker website, open it, and drag the Docker icon into your Applications folder. Open the app to finish the background setup.
* **Podman Desktop:** A popular, open-source alternative to Docker Desktop. Download the macOS installer from the Podman website, run it, and follow the setup wizard to initialize the background virtual machine.
* **Rancher Desktop:** Built for Kubernetes and container management. Download the macOS installer from the Rancher Desktop website. Move it to Applications and run it; it will prompt you to choose your container engine (select `dockerd`).
* **OrbStack:** A fast, lightweight, and highly efficient alternative specifically built for Mac. Download it from the OrbStack website and drag it to your Applications folder. It serves as a direct drop-in replacement for Docker Desktop.

### Windows

* **Docker Desktop:** Download the `.exe` installer from Docker's website. Run it and ensure the "Use WSL 2 instead of Hyper-V" option is checked (this makes it run much faster). Restart your computer when prompted.
* **Podman Desktop:** Download the Windows installer from the Podman website. Run the `.exe` and follow the prompts. It will guide you through setting up WSL (Windows Subsystem for Linux) if you do not already have it.
* **Rancher Desktop:** Download the Windows `.exe` installer from the Rancher website. Run the setup, and upon opening, select `dockerd` as your container engine and enable WSL integration.
* **WSL2 + Docker CLI:** For those who prefer the command line without a heavy user interface. Open PowerShell as an administrator and type `wsl --install` to install the Windows Subsystem for Linux (usually Ubuntu). Once installed, open your new Ubuntu terminal and use the command `sudo apt install docker.io` to install the core Docker engine.

### Linux

* **Docker Desktop:** Download the `.deb` or `.rpm` package (depending on your distribution, like Ubuntu or Fedora) from the Docker website. Use your system's package manager to install it (e.g., `sudo apt install ./docker-desktop.deb`).
* **Podman Desktop:** The easiest way to install on Linux is via Flatpak. If Flatpak is enabled on your system, you can install it directly from Flathub using your software center or terminal.
* **Rancher Desktop:** Add the Rancher Desktop repository to your system's package manager (instructions vary slightly between Ubuntu, Fedora, etc.) or download and run the provided `.deb` or `.rpm` files from their releases page.
* **Portainer:** Portainer is actually a management interface that runs *inside* Docker. First, install a basic Docker engine using your package manager (e.g., `sudo apt install docker.io`). Then, use a single Docker command (found on Portainer's documentation) to download and launch the Portainer container, which you access via your web browser.
* **LXD/LXC:** These are system containers, slightly different from Docker's application containers. On most modern Linux systems (especially Ubuntu), you can install them using the snap package manager by running `sudo snap install lxd`, followed by `lxd init` to configure the storage and network.




# AI Proxy

An AI Proxy (specifically in the context of OpenClaw and AI models) is a
middleware service that sits between the autonomous OpenClaw agent and the Large
Language Models (LLMs) it uses (such as OpenAI, Anthropic, or local models).

Rather than OpenClaw communicating directly with an API provider, it sends all
requests to this intermediary. The proxy acts as a control plane for cost,
safety, and model flexibility, turning OpenClaw into a "client" and the user
into the "operator".

## How The AI Proxy Interacts With AI Models

* **Unified Endpoint**: It exposes an OpenAI- or Anthropic-compatible API
  endpoint.

* **Model Agnostic**: It allows swapping between cloud providers (e.g., GPT-4
  to Claude 3.5 Sonnet) or local models (e.g., via Ollama) without changing the
  OpenClaw configuration.

* **Cost & Rate Limiting**: It acts as a traffic manager that can cache
  frequently used responses, log requests, and prevent API bill spikes.

* **Performance Tracking**: It measures latency and error patterns to enhance
  reliability.

## How The AI Proxy Interacts With OpenClaw

In the specific context of OpenClaw, this proxy is critical due to the agent’s
autonomous, local-first nature:

* **API Key Rotation (CLIProxy)**: It manages multiple API keys, rotating
  through them to avoid hitting rate limits with services like OpenRouter.

* **Tool Call Injection (ClawCut)**: Specialized proxies like "ClawCut" can
  clean up JSON clutter, preventing smaller, cheaper local models from
  experiencing "cognitive overload" when handling complex tool calls.

* **Network Privacy (Mobile Proxies)**: When OpenClaw uses browser automation
  (CDP), the proxy routes traffic through mobile IPs to prevent IP-based
  blocking or website fingerprinting.

* **Workflow Optimization**: It transforms the synchronous nature of LLM calls
  into an asynchronous "mailbox" approach, allowing the agent to handle multiple
  messages and batch replies without stalling.

## Prompt [admin]

**Role**: OpenClaw Installation Expert, AI Proxy Expert

**Context**: I am setting up dockerized OpenClaw on a Macbook Air with 16GB of
RAM. I will be using dockerized LiteLLM as an AI Proxy to provide prompt
classification (simple, medium, complex, reasoning), model failover, etc.
Target your text to someone who is unfamiliar with OpenClaw and wants to learn
both the task at hand (installing LiteLLM) and the overall OpenClaw ecosystem
and architecture.

**Task**: Provide detailed instructions for how to install, use, and maintain
LiteLLM (running in Docker via OrbStack), with the understanding that when
OpenClaw onboarding occurs, we will be selecting LiteLLM as the
"Model/auth provider".

- The following sections should exist in the markdown you produce as the output
  for this prompt.

   - **Before onboarding**: Provide an overall summary of what happens here and why.
     Provide instructions on how to create an $OPENCLAW_ROOT/litellm-proxy
     directory within which all files in this section are placed. Discuss
     prompt complexity (simple, medium, complex, reasoning). Create subsections
     for the following:

      - **File: .env**: discuss its use-cases and provide an example .env file
        defining GEMINI_API_KEY_{SIMPLE,MEDIUM,COMPLEX,REASONING,EMBEDDING},
        LITELLM_PORT, and LITELLM_MASTER_KEY.  Use these in all other files
        as appropriate.

      - **File: config.yaml**: discuss its purpose, discuss LiteLLM's Semantic Auto
        Router and Complexity Router, and provide example contents that
        includes:
         - models named {simple,medium,complex,reasoning}-model that use the
           most appropriate gemini models for each complexity level
         - an embedding model for use with LiteLLM's Semantic Router
         - an auto-router endpoint for LiteLLM's Auto Router

      - **File: router.json**: discuss its purpose and provide an example file
        containing 10 representative utterances for each of {simple,medium,complex,reasoning}-model
        and assigning an appropriate score_threshold for each.

      - **File: docker-compose.yml**: discuss its purpose, provide an initial version of
        the file (use variables from .env as appropriate).

      - **Installation**: show how to start litellm up within docker, and
        provide two ways to test that LiteLLM is working (a bash command that
        uses curl to get http://localhost:4000/v1/models, and a python script
        that posts to http://localhost:4000/v1/chat/completions

      - **Lifecycle and Maintenance**: Discuss details related to LiteLLM
        lifecycle and maintenance. When are restarts needed? How are they done?
        How is LiteLLM upgraded and how often should it be upgraded? How does
        one monitor the health of LiteLLM?

   - **During onboarding**: Provide details for what needs to be done during
     opencrawl onboarding (via docker-setup.sh) to configure LiteLLM properly.

   - **After onboarding**: Provide details of what needs to be done to set up
     LiteLLM after opencrawl onboarding has finished.

   - **Common Setup Gotchas**: Discuss things like "IsADirectoryError: [Errno
     21] Is a directory: '/app/config.yaml'", port conflicts, environment
     variable scope, YAML indentation errors, missing /v1 in Base Url, Docker
     Network Isolation, and any other common issues that occur for first time
     OpenClaw onboarders.

**Format**: You are to form a markdown document providing detailed instructions
on how to set up LiteLLM in Docker for use with OpenClaw in Docker. Provide two
versions of the output: 1) the markdown as-is (so I can see it formatted in the
Gemini UI), 2) the markdown encapsulated in &lt;pre&gt;&lt;code&gt; ...
&lt;/code&gt;&lt;/pre&gt; (so I can cut-and-paste the raw unformatted markdown
syntax elsewhere).

## Installation & Maintenance

### LiteLLM

This documentation provides the architectural overview and operational steps for deploying LiteLLM as an AI proxy for OpenClaw using Docker and OrbStack.

LiteLLM acts as an API gateway. It standardizes OpenClaw's outbound model requests into the OpenAI API format, handling dynamic routing, load balancing, and failover independent of the OpenClaw application layer. This separation of concerns ensures OpenClaw remains agnostic to underlying model changes or rate limits.

#### Before onboarding

Before running OpenClaw's setup routine, the LiteLLM proxy must be active and configured. The proxy uses a semantic routing architecture. When OpenClaw submits a prompt, LiteLLM vectorizes the prompt using an embedding model and compares it against predefined clusters of utterances. It calculates the semantic distance and routes the prompt to the most efficient model (simple, medium, complex, or reasoning) based on predefined thresholds.

Create the proxy directory:
```bash
mkdir -p $OPENCLAW_ROOT/litellm-proxy
cd $OPENCLAW_ROOT/litellm-proxy
```
All files below must be created within this directory.

##### File: .env
This file stores your environmental configuration and secrets, keeping them out of source control.
```env
LITELLM_PORT=4000
LITELLM_MASTER_KEY=sk-openclaw-master-key-31415
GEMINI_API_KEY_SIMPLE=your_api_key_here
GEMINI_API_KEY_MEDIUM=your_api_key_here
GEMINI_API_KEY_COMPLEX=your_api_key_here
GEMINI_API_KEY_REASONING=your_api_key_here
GEMINI_API_KEY_EMBEDDING=your_api_key_here

 This is a hack to work around a problematic assumption made in
 https://github.com/aurelio-labs/semantic-router/blob/371cbf737d255a1ec81874a1dda4738e7e19879a/semantic_router/encoders/litellm.py#L59
GEMINI_API_KEY=${GEMINI_API_KEY_EMBEDDING}
```

##### File: config.yaml
This file maps your API keys to specific model endpoints and configures the routing logic. The `router_settings` block dictates how the Semantic Auto Router utilizes embeddings to assess prompt complexity.
```yaml
model_list:
  # The Capability Tiers
  - model_name: simple-model
    litellm_params:
      model: gemini/gemini-3.1-flash-lite
      api_key: os.environ/GEMINI_API_KEY_SIMPLE
  - model_name: medium-model
    litellm_params:
      model: gemini/gemini-3.1-flash-lite-preview
      api_key: os.environ/GEMINI_API_KEY_MEDIUM
  - model_name: complex-model
    litellm_params:
      model: gemini/gemini-3.1-pro-preview
      api_key: os.environ/GEMINI_API_KEY_COMPLEX
  - model_name: reasoning-model
    litellm_params:
      model: gemini/gemini-3-deep-think
      api_key: os.environ/GEMINI_API_KEY_REASONING

  # Fallback models
  - model_name: complex-model-fallback
    litellm_params:
      model: gemini/gemini-2.5-pro
      api_key: "os.environ/GEMINI_API_KEY_MEDIUM"
  - model_name: reasoning-model-fallback
    litellm_params:
      model: gemini/gemini-3.1-pro-preview
      api_key: "os.environ/GEMINI_API_KEY_COMPLEX"

  # Embedding Model (Required for Semantic Router)
  - model_name: prompt-embedding-model
    litellm_params:
      model: gemini/gemini-embedding-001
      api_key: os.environ/GEMINI_API_KEY

  # The Semantic Router Endpoint
  - model_name: semantic-router
    litellm_params:
      model: auto_router/semantic
      auto_router_config_path: router.json
      auto_router_default_model: medium-model
      auto_router_embedding_model: prompt-embedding-model

  # The Complexity Router Endpoint
  - model_name: complexity-router
    litellm_params:
      model: complexity_router/complexity
      complexity_router_default_model: medium-model
      complexity_router_simple_model: simple-model
      complexity_router_complex_model: complex-model
      complexity_router_reasoning_model: reasoning-model

router_settings:
  fallbacks:
    - {"complex-model": ["complex-model-fallback"]}
    - {"reasoning-model": ["reasoning-model-fallback"]}

litellm_settings:
  drop_params: true
  num_retries: 2
  allowed_fails: 3

general_settings:
  master_key: "os.environ/LITELLM_MASTER_KEY"
```

##### File: router.json

This file defines the semantic clusters. The router calculates the cosine
similarity between the incoming prompt and these utterances. If the similarity
exceeds the `score_threshold`, the prompt is routed to the corresponding
`model_name`.

```json
{
  "encoder_type": "litellm",
  "encoder_name": "prompt-embedding-model",
  "routes": [
    {
      "name": "simple-model",
      "score_threshold": 0.80,
      "utterances": [
        "What is the capital of Australia?",
        "Translate 'Where is the library?' to French.",
        "What is the atomic number of Gold?",
        "Convert 100 degrees Fahrenheit to Celsius.",
        "Spell the word 'accommodate'.",
        "Who wrote '1984'?",
        "What is 15% of 850?",
        "List the primary colors.",
        "How many days are in a leap year?",
        "What is the chemical formula for water?",
        "Define the word 'ubiquitous'.",
        "Who was the first person to walk on the moon?",
        "What is the largest ocean on Earth?",
        "Give me a synonym for 'happy'.",
        "What year did the Titanic sink?",
        "Convert 5 kilometers to miles.",
        "What is the square root of 144?",
        "Name the planets in our solar system.",
        "How many continents are there?",
        "What is the speed of light in a vacuum?",
        "Who painted the Mona Lisa?",
        "What is the currency of Japan?",
        "Write a regular expression to match an email address.",
        "What is the boiling point of water at sea level?",
        "Format this unformatted JSON string into a readable structure."
      ]
    },
    {
      "name": "medium-model",
      "score_threshold": 0.80,
      "utterances": [
        "Summarize the plot of 'The Matrix' in three paragraphs.",
        "Write a Python script to parse a CSV file and output JSON.",
        "Draft a professional email declining a job offer.",
        "Explain the difference between TCP and UDP to a junior developer.",
        "Write a basic SQL query to join a 'users' table with an 'orders' table.",
        "What are the pros and cons of using a NoSQL database?",
        "Debug this simple React component that isn't updating state correctly.",
        "Explain the concept of closure in JavaScript with an example.",
        "Write a bash script to find and delete files older than 30 days.",
        "Outline a marketing strategy for a new coffee shop.",
        "Compare and contrast REST and GraphQL APIs.",
        "Write a function in Go to reverse a string in place.",
        "Explain how a DNS resolution works step-by-step.",
        "Draft a project proposal for implementing a new CRM system.",
        "What are the key principles of Object-Oriented Programming?",
        "Write a Dockerfile for a standard Node.js application.",
        "Explain the concept of Big O notation and give examples of O(1) and O(n).",
        "Describe the MVC architectural pattern.",
        "Write a unit test for a function that calculates the Fibonacci sequence.",
        "How does garbage collection work in Java?",
        "Explain the differences between Git Merge and Git Rebase.",
        "Write a Terraform script to provision a basic AWS S3 bucket.",
        "Describe the lifecycle hooks in a Vue.js application.",
        "Explain what a JWT (JSON Web Token) is and how it is used.",
        "Write a simple REST API in Express.js with a GET and POST endpoint."
      ]
    },
    {
      "name": "complex-model",
      "score_threshold": 0.80,
      "utterances": [
        "Design a microservices architecture for a high-traffic ticketing system.",
        "Write a Rust program implementing a concurrent web scraper using asynchronous I/O.",
        "Analyze the security implications of using local storage versus HTTP-only cookies for JWTs.",
        "Explain the Paxos consensus algorithm and its failure modes.",
        "Optimize this nested SQL query that is causing full table scans on a billion-row table.",
        "Design a rate-limiting middleware using Redis and explaining the chosen algorithm.",
        "Explain the mechanics of an SQL injection attack and how parameterized queries prevent it.",
        "Architect a data pipeline to process 10TB of telemetry data per day using Kafka and Spark.",
        "Write a Kubernetes deployment manifest utilizing init containers, probes, and resource limits.",
        "Explain the B-Tree data structure and why it is optimal for database indexing.",
        "Debug this C++ code suffering from a race condition and a potential deadlock.",
        "Design a multi-region active-active failover strategy for a global web application.",
        "Explain the internal workings of the V8 JavaScript engine's garbage collector.",
        "Write a Python script implementing a custom LRU cache thread-safe decorator.",
        "Analyze the trade-offs between Event Sourcing and traditional CRUD state management.",
        "Implement a distributed lock using ZooKeeper.",
        "Explain how CPU cache coherence protocols (like MESI) function in multi-core processors.",
        "Design an anomaly detection system for network traffic logs.",
        "Write a parser in C for a custom, binary network protocol.",
        "Explain the differences in memory management between Rust and C++.",
        "Architect a real-time collaborative text editor backend using Operational Transformation.",
        "Analyze a Linux kernel panic log to identify a faulty driver.",
        "Implement a custom memory allocator in C.",
        "Design a scalable search engine architecture utilizing inverted indexes.",
        "Explain the cryptography behind elliptic curve Diffie-Hellman (ECDH) key exchange."
      ]
    },
    {
      "name": "reasoning-model",
      "score_threshold": 0.80,
      "utterances": [
        "Prove that the square root of 2 is irrational.",
        "Solve the Monty Hall problem and provide a rigorous mathematical proof for why switching is optimal.",
        "Analyze the ethical implications of deploying autonomous weapons systems.",
        "If P=NP were proven true, what would be the specific cryptographic and economic consequences?",
        "Formulate a logical argument resolving the Ship of Theseus paradox.",
        "Evaluate the architectural trade-offs between eventual consistency and linearizability.",
        "Explain Gödel's First Incompleteness Theorem and its implications for formal axiomatic systems.",
        "Deduce the outcome of this complex game theory scenario involving incomplete information.",
        "Critically analyze the simulation hypothesis from a physical and computational perspective.",
        "Provide a step-by-step mathematical proof of Euler's formula.",
        "Evaluate the ontological arguments for the existence of abstract mathematical objects.",
        "Resolve a specific edge-case paradox in special relativity involving simultaneous events.",
        "Analyze the logical structure of a self-referential paradox and propose a resolution.",
        "Determine the optimal resource allocation strategy in a complex economy using linear programming.",
        "Evaluate the philosophical concept of free will in a deterministic universe.",
        "Provide a rigorous proof for the Pythagorean theorem using similar triangles.",
        "Analyze the fundamental limits of computation as defined by the Halting Problem.",
        "Formulate a comprehensive risk model for a novel financial derivative.",
        "Evaluate the epistemological challenges of determining consciousness in artificial intelligence.",
        "Solve a multi-layered cryptogram utilizing frequency analysis and known-plaintext attacks.",
        "Analyze the thermodynamic limits of energy efficiency in computation.",
        "Construct a formal proof in propositional calculus for a complex logical theorem.",
        "Evaluate the societal impacts of universal basic income using distinct macroeconomic models.",
        "Explain the concept of quantum entanglement and how it violates local realism.",
        "Formulate a strategy to stabilize a complex, chaotic system using control theory methodologies."
      ]
    }
  ]
}
```

##### File: docker-compose.yml

This defines the container specification. It mounts the configuration files and
exposes the proxy port.

```yaml
version: "3.9"
services:
  litellm:
    container_name: litellm-proxy
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "${LITELLM_PORT:-4000}:4000"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./router.json:/app/router.json
    env_file:
      - .env
    command: [ "--config", "/app/config.yaml", "--port", "${LITELLM_PORT:-4000}" ]
```

Note the explicit version in `services.litellm.image` (it is common to use
`ghcr.io/berriai/litellm:main-latest` but this is a deviation from rigorous
infrastructure management principles. It violates the principle of immutable
infrastructure. If you deploy main-latest today, and deploy main-latest next
month, you may be running two completely different software binaries under the
exact same identifier. If a routing bug occurs, you have no cryptographic hash
or version number to reference against the upstream changelog. Because of this,
it is recommended that you always pin to explicit, immutable release tags (e.g.,
v1.35.0).

If we pin LiteLLM to a specific version, when do we upgrade to a new version?
LLM Runners are critical infrastructure, which requires prioritizing stability
over novel features. You should only execute an upgrade under three specific
conditions:

1. **Security**: A CVE is published that affects the proxy's network boundary.

2. **Required Capabilities*: An AI provider (e.g. Google) releases a new model
   family (e.g., Gemini 4.0) that OpenClaw requires, and your current LiteLLM
   version lacks the internal mapping to parse its specific API schema.

3. **Critical Bug Fixes**: You encounter a reproducible bug in routing or
   cost-tracking that is explicitly resolved in the upstream changelog.

The list of releases are available at
https://github.com/BerriAI/litellm/releases. If an upgrade is deemed necessary,
do the following:

* Update LITELLM_VERSION in `.env`

* Execute the following commands
```
docker compose pull
docker compose up -d --force-recreate
python litellm-test.py
python test_thresholds.py
```

Note that using `docker compose up -d --force-recreate` is sufficient, and much
more gentle than `docker compose down && docker compose up -d`, which is quite
violent (severs all active TCP connections, any adjacent containers relying on
the gateway IP, like OpenClaw, Redis, Postgres, etc, will drop)

##### Installation

Deploy the proxy using standard Docker commands:

```bash
docker compose up -d
```
Verify the proxy is operational via cURL:
```bash
curl -X GET "http://localhost:4000/v1/models" \
  -H "Authorization: Bearer sk-openclaw-master-key-31415"
```
Verify the semantic routing is functioning via Python:
```python
import requests
import json

url = "http://localhost:4000/v1/chat/completions"
headers = {
  "Content-Type": "application/json",
  "Authorization": "Bearer sk-openclaw-master-key-31415"
}
data = {
  "model": "semantic-router",
  "messages": [{"role": "user", "content": "Write a bash script to backup a database."}]
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(json.dumps(response.json(), indent=2))
```

##### Lifecycle and Maintenance

Dockerizing LiteLLM isolates the environment but requires specific lifecycle management to ensure state consistency.

###### When to Restart:

The LiteLLM container caches configurations on startup. You must tear down and
recreate the container when modifying infrastructure files. Running `docker
compose restart` is often insufficient for environment variables.

* **Modified `.env`**: Requires recreation.

* **Modified `docker-compose.yml`**: Requires recreation.

* **Modified `config.yaml`**: LiteLLM supports hot-reloading for some
  configuration changes, but a hard restart is the safest way to guarantee the
  new state is applied without residual cache artifacts.

**Restart Command:**

```bash
docker compose down && docker compose up -d
```

###### Upgrading LiteLLM

Because the `docker-compose.yml` targets `main-latest`, the container will not
automatically update to a new version simply by restarting. You must explicitly
pull the new image layer before recreating the container.

```bash
docker compose pull litellm
docker compose down && docker compose up -d
```

###### Health Monitoring:

Monitor the container logs for routing errors, authentication failures, or
provider timeouts using:

```bash
docker compose logs -f litellm
```

#### During onboarding

When executing the OpenClaw `docker-setup.sh` script (or its equivalent
configuration phase), you must configure it to utilize the proxy rather than
direct provider APIs.

* **Model Provider:** Select `openai` (LiteLLM emulates the OpenAI API).

* **API Key:** Provide your `LITELLM_MASTER_KEY` (`sk-openclaw-master-key-31415`).

* **Base URL:** Set this to `http://host.docker.internal:4000/v1`. Because
OpenClaw runs in a Docker container via OrbStack, `localhost` will resolve to
OpenClaw's container, not the LiteLLM container. `host.docker.internal`
explicitly routes out to the host network bridge, allowing OpenClaw to reach
LiteLLM.

* **Model Name:** Specify `semantic-router` to invoke the semantic routing engine
defined in your configuration.

#### After onboarding

* **Refining Utterances**: Continually update the `router.json` file as you
discover edge cases in the prompt routing logic. New utterances keep the
embedding model accurate when selecting the right tier.

* **Failovers and Retries**: Periodically re-evaluate failbacks to ensure they
are correct and that secondary models are handling failover traffic effectively
without exceeding their own quotas.

#### Common Setup Gotchas

* **`IsADirectoryError: [Errno 21] Is a directory: '/app/config.yaml'`**: This
occurs if you run `docker compose up` before actually creating the `config.yaml`
file. Docker assumes the missing file is meant to be a directory and creates an
empty folder in your host filesystem. Stop the container, remove the erroneous
directory (`rm -rf config.yaml`), create the actual file, and restart.

* **Missing `/v1` in Base URL**: OpenClaw's underlying HTTP client often
requires the specific API version endpoint. If requests fail with 404s, ensure
your OpenClaw Base URL is strictly `http://host.docker.internal:4000/v1` and not
just `http://host.docker.internal:4000`.

* **Docker Network Isolation**: If OpenClaw fails to connect entirely, it is a
network routing issue. OrbStack handles `host.docker.internal` reliably, but if
you switch environments, you may need to place both containers on a shared,
explicit Docker bridge network.

* **YAML Indentation Errors**: `config.yaml` is strictly typed. Ensure spaces
(not tabs) are used, and that `litellm_params` are correctly nested under each
item in the `model_list`.

* **Port Conflicts**: If your defined port is already bound by another service,
Docker will fail to start the container. Modify the `.env` variable to an open
port (e.g., `4001`) and update your OpenClaw setup accordingly.

* **Environment Variable Scope**: Ensure there are no spaces around the equals
sign in your `.env` file (e.g., `KEY = value` will fail; use `KEY=value`).


# OpenClaw

## Installation

Questions to resolve:
- What is your AI Provider? Is it accessed via a publicly routable internet
  endpoint (eg https://openrouter.ai/api/v1), or does it require internal
  Docker bridge networking (eg. LiteLLM, etc)?
   - the answer determines whether we can use docker-setup.sh (public endpoint),
     or must use a declarative approach (internal bridge networking)

### File: docker-compose.yml

Here is the definitive `docker-compose.yml` for your OpenClaw and LiteLLM stack, followed by a rigorous breakdown of its components.

```yaml
services:
  openclaw-gateway:
    build: .
    image: openclaw:local
    container_name: openclaw-gateway
    restart: unless-stopped
    ports:
      - "18789:18789"
    volumes:
      - ~/.openclaw:/home/node/.openclaw
      - ~/openclaw-workspace:/home/node/.openclaw/workspace
    environment:
      - OPENCLAW_GATEWAY_BIND=lan
      - OPENAI_API_KEY=sk-litellm-proxy-key
      - OPENAI_BASE_URL=http://<litellm_container_name>:4000/v1
    networks:
      - ai-net

networks:
  ai-net:
    external: true
```

#### 1. Services & Build Configuration
* `build: .`: This instructs Docker to build the image from the Dockerfile in the current directory (which you cloned via git). This is critical for OpenClaw because running the `local` build ensures your container's code exactly matches the repository version you pulled, avoiding version mismatch errors between the Node.js gateway and the expected memory structures.
* `image: openclaw:local`: Tags the resulting build locally so Docker does not attempt to pull a non-existent image from a public registry.
* `restart: unless-stopped`: Ensures the daemon persists across host reboots or unexpected crashes, unless you explicitly issue a `docker compose down` command.

#### 2. Network Bindings (Ports)
* `ports: ["18789:18789"]`: Maps port 18789 on your macOS host to port 18789 inside the container. This specific port serves the OpenClaw Control UI, allowing you to access the web interface via `http://localhost:18789` in your local browser.

#### 3. Persistent State (Volumes)
OpenClaw is highly stateful but relies entirely on the filesystem instead of a relational database.
* `~/.openclaw:/home/node/.openclaw`: Mounts the configuration directory. This is where OpenClaw stores its `.env` file (containing your UI login token) and internal routing data. If this volume is lost, you lose access to the UI and your configuration state.
* `~/openclaw-workspace:/home/node/.openclaw/workspace`: Mounts the operational directory. This is where OpenClaw stores long-term memory, session transcripts, and custom skill definitions (`SKILL.md` files). This is the most critical data volume to back up.

#### 4. Environment Injection (The Declarative Core)
This section replaces the `docker-setup.sh` script entirely.
* `OPENCLAW_GATEWAY_BIND=lan`: Instructs the Gateway to accept connections from outside its own local container loopback. Without this, you would not be able to access the Control UI from your Mac browser.
* `OPENAI_API_KEY=sk-litellm-proxy-key`: The authentication token expected by your LiteLLM instance.
* `OPENAI_BASE_URL=http://<litellm_container_name>:4000/v1`: Re-routes all internal LLM requests away from public servers and directly to your local proxy container over the shared Docker network.

#### 5. Network Topology
* `networks: [ai-net]`: Connects the OpenClaw gateway to a specific Docker bridge network named `ai-net`.
* `external: true`: Declares that `ai-net` is managed outside of this specific compose file. This is mandatory because your LiteLLM container was spun up independently and is already attached to this network. Without `external: true`, Docker Compose would attempt to create a new, isolated network and OpenClaw would be unable to resolve the LiteLLM container name via DNS.

## Prompt Complexity Analysis

[Internal]: [AI/OC: Prompt Complexity Analysis](Discussed in https://gemini.google.com/u/1/app/d95fc3b1ddb09f4a)

Assessing prompt complexity to route requests dynamically—often referred to as
semantic or complexity routing—is a fundamental requirement for scaling AI
architectures efficiently. The goal is to avoid wasting expensive inference
compute (like Claude 3.5 Sonnet or OpenAI o3) on trivial tasks (like simple
formatting or basic Q&A) that a highly optimized model (like DeepSeek, Llama 3
8B, or Gemini Flash) can handle at a fraction of the cost.

### 1. Assessment Methodologies

Before evaluating specific tools, we must define the computational methods used
to calculate complexity.

* **Pre-cognitive (Deterministic Routing)**: TODO(wmh): Add summary or collapse following points into paragraph
    * **PII / Data Sovereignty Routing**: A fast heuristic or regex pass that identifies Personally Identifiable Information (PII) or proprietary API keys. If detected, the prompt is hard-routed to your local ollama-runner, bypassing cloud models entirely, regardless of complexity.
    * **Context-Window Routing (Token Counting)**: A deterministic check of the prompt length. If the prompt + context history exceeds 8k tokens, it bypasses the fast/cheap local models and routes directly to a model with a 128k+ window.
    * **Budget-Aware Routing**: The proxy (LiteLLM) checks the current token spend for the hour/day. If the budget limit is approaching, it artificially downgrades the complexity routing, forcing traffic to cheaper models to prevent pipeline halting.

* **Heuristic / Rule-based Scoring (Lexical Routing):** Analyzes the raw text of the
  prompt against predefined dimensions. It looks for reasoning markers (e.g.,
  "think step by step", "analyze"), structural complexity (JSON schemas, heavy
  formatting), code presence (e.g., `def`, `class`, markdown code blocks), and
  raw token length.

* **Vector Similarity (Semantic Routing):** Uses a fast embedding model to map the
  incoming prompt to a vector space. It compares this vector against a stored
  database of known "simple" or "complex" queries.

* **LLM-as-a-Judge (Predictive Routing):** Injects a micro-model (often a
  highly quantized local model or a fine-tuned classifier) into the pipeline.
  This model reads the prompt and outputs a discrete complexity score (1-10) or
  tier before the primary inference occurs.

* **Reactive Cascading (Fallback Routing):** A trial-and-error approach. The
  prompt is automatically routed to a low-tier model. If the output fails a
  specific validation check (e.g., broken JSON, incomplete code, or a
  self-reported low confidence score), the system retries with a high-tier
  model.

### 2. Tool & Ecosystem Analysis

#### ClawRouter

ClawRouter is an agent-native, open-source LLM router built heavily around the
OpenClaw ecosystem, explicitly designed to operate without human intervention.

* **Mechanism:** It utilizes a purely heuristic approach, applying a
  14-dimension weighted scoring algorithm (evaluating code presence, reasoning
  markers, length, etc.) to classify the prompt in under 1ms.

* **Tiering Structure:** It rigidly maps queries into four brackets: `SIMPLE`
  (routed to DeepSeek or similar), `MEDIUM` (GPT-4o-mini / Gemini Flash), `COMPLEX` (Claude 3.5 Sonnet / Pro models), and `REASONING` (o3 / Grok-3).

* **Cost-Benefit:** Highly optimal for autonomous agent loops. Because it
  runs 100% locally and uses heuristics, it introduces zero external API calls and negligible latency. It also uniquely integrates x402 USDC micropayments via Base/Solana, allowing agents to pay for their own compute per-request rather than relying on centralized API keys.

#### LiteLLM (Complexity Router vs. Auto Router)

LiteLLM operates as a proxy server and provides two distinct paradigms for
routing.

* **Complexity Router:** Similar to ClawRouter, this is a rule-based engine.
  It analyzes the prompt structure locally to determine complexity.

    * *Ramifications:* <1ms latency, zero API cost. Best for environments
      where you want to strictly gatekeep expensive models based on hard constraints (e.g., only route to GPT-4 if the prompt exceeds 2,000 tokens or requests Python code).

* **Auto Router (Semantic):** This uses the Vector Similarity approach. It
  requires an embedding model (like `text-embedding-3-small`) to convert the
  prompt into a vector and match it against defined routes/utterances.

    * *Ramifications:* Adds 100ms - 500ms of latency and a fractional cost
      for the embedding tokens. It is highly accurate for intent-based routing (e.g., detecting if a user is asking a customer support question vs. a technical engineering question) but slower than rule-based scoring.

#### OpenClaw Agent Runner (`before_model_resolve`)

OpenClaw functions as a continuous agentic loop (Think-Act-Observe) utilizing a
"Lane Queue" for deterministic execution. The `before_model_resolve` plugin hook
sits inside the Agent Runner's prompt assembly line.

* **Mechanism:** When an agent intent is discovered, but before the model is
  invoked, this hook can execute custom arbitrary logic. You can build a plugin
  that triggers a local Llama 3 model to act as a judge, or run a custom regex
  suite over the retrieved `MEMORY.md` context.

* **Cost-Benefit:** Offers absolute architectural freedom. You can write
  custom TypeScript logic to check local system state, rate limits, or user
  permissions before assigning a tier. However, if your plugin invokes a
  secondary LLM to judge complexity, you introduce severe latency penalties
  (500ms to 2s) to the critical path of the agent loop.

#### Framework-Level Cascading (e.g., LangChain / LlamaIndex Fallbacks)

Rather than predicting complexity, these frameworks often implement reactive
routing.

* **Mechanism:** Execute the prompt on a low-tier model. Pass the output to
  an output parser. If the parser throws an exception, catch the error and
  execute the prompt on a high-tier model.

* **Cost-Benefit:** Zero upfront engineering required, but possesses the
  worst latency profile. A failed generation on a cheap model still takes time.
  If 30% of your requests fail on the low tier and get bumped to the high tier,
  your average p99 latency will be disastrously high for end-users.


### 3. Latency & Price Ramifications Summary

| Assessment Method | Example Tooling | Added Latency | Added Cost | Accuracy / Efficacy |
| :--- | :--- | :--- | :--- | :--- |
| **Local Heuristics** | ClawRouter, LiteLLM Complexity Router | **< 1ms** | **$0.00** | Good for structural/code routing. Fails on nuanced semantic complexity. |
| **Semantic Embedding** | LiteLLM Auto Router | **100ms - 500ms** | **~$0.02 / 1M tokens** | Excellent for intent classification. Requires maintaining an utterance database. |
| **LLM-as-a-Judge** | Custom OpenClaw Plugin | **500ms - 2000ms** | **Variable (Judge Model)** | Highest accuracy for abstract reasoning. Too slow for high-frequency agent loops. |
| **Reactive Cascading** | LangChain Fallbacks | **1000ms+ (on failure)** | **Cost of failed run** | Guarantees final output quality, but creates severe UX bottlenecks upon failure. |

# Channels
# Knowledge Acquisition
# Local Models (LLM Runners)

We discussed local models and LLM runners back in the 'Brains' section, but
this is where we talk about how to actually install and run local models.
As discussed in that previous section, there are numerous different categories
and implementations of LLM runners. This section will grow over time as we
explore details of how to properly install specific LLM runners.

## Ollama

# Local Redis (caching)
# Local Postgres (bitlogging)
