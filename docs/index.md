Meta<Claw> is an installation framework designed to deploy and manage a secure, cost-effective, and capable personal AI ecosystem. It provides an automated, modular infrastructure that allows non-technical individuals to instantly deploy a swarm of sibling technologies that give their AI agents vastly more capability, reliability, and security.


# Meta<Claw>: Your Personal AI Installation Framework

## Overview

Meta<Claw> is a comprehensive installation framework designed to deploy and
manage a secure, cost-effective, and highly capable personal AI ecosystem. While
front-end AI gateways (like OpenClaw or n8n) provide the user interface and
basic agent logic, they cannot function securely or efficiently in a vacuum.
They require a surrounding ecosystem of databases, memory caches, secure
sandboxes, and logging pipelines to reach their full potential.

Meta<Claw> removes the immense technical complexity of configuring this
ecosystem. It provides an automated, modular infrastructure that allows
non-technical individuals to instantly deploy a swarm of sibling technologies
that give their AI agents vastly more capability, reliability, and security.


### Vocabulary: Services, Providers, and Skills

To understand how Meta<Claw> functions, it is crucial to distinguish between
three layers of the ecosystem:

1.  **Services:** The broad categories of infrastructure required to run an AI
    (e.g., "Long-Term Memory" or "AI Proxy"). Meta<Claw> manages these.
2.  **Providers:** The specific software choices used to fulfill a service's
    role (e.g., using "PostgreSQL" to fulfill the "Long-Term Memory"
    requirement, or "LiteLLM" for the "AI Proxy"). Meta<Claw> installs and
    orchestrates these.
3.  **Skills/Plugins:** The actual capabilities the AI uses to do work (e.g.,
    "Search the Web", "Create a Calendar Event"). These are managed directly
    within the Gateway (like OpenClaw), though they often rely on the
    infrastructure Meta<Claw> provides to function safely.

The goal of Meta<Claw> is to get you up and running with a production-grade
infrastructure with as little effort as possible, freeing you to focus entirely
on building your agents and defining their skills.

## Table Of Contents

* **[ARCHITECTURE.md](ARCHITECTURE.md)**: Details the framework's core
  engineering philosophy, hardware scaling strategies, and routing intelligence.
* **[SERVICES.md](SERVICES.md)**: The canonical registry categorizing and
  explaining the purpose of every infrastructure service supported by the
  framework.
* **[HOWTO.md](HOWTO.md)**: Standard Operating Procedures (SOPs) for end-users.
  Guides on resetting state, upgrading, and day-to-day management.
* **[PROFILES.md](PROFILES.md)**: Explains the distributed cluster
  orchestration and how providers are assigned to specific hardware nodes.
* **[ROADMAP.md](ROADMAP.md)**: The prioritized strategy for future framework
  expansion and capability integration.
* **[LLM.md](LLM.md)**: Strict operational rules, epistemic boundaries, and
  formatting protocols for AI agents contributing to this codebase. *(For LLM
  Contributors Only).*

## Useful URLs

The following URLs are critical for managing your Meta<Claw> infrastructure and
its services.

### Core Framework
* **OpenClaw Dashboard (Local):** [http://localhost:18789/](http://localhost:18789/)
* **OpenClaw Dashboard (Tailscale Remote):** `http://[Your-Tailscale-IP]:18789/`

### Service Management
* **Tailscale Admin Console (Machines):**
  [https://login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
* **Tailscale Auth Keys (Generation):**
  [https://login.tailscale.com/admin/settings/keys](https://login.tailscale.com/admin/settings/keys)
* **VictoriaLogs UI (vmui):** [http://localhost:9428/select/vmui](http://localhost:9428/select/vmui)
* **LiteLLM API Health/Models:** [http://localhost:4000/v1/models](http://localhost:4000/v1/models)

## Installation Wizard

Welcome to the Meta<Claw> setup wizard. This window serves as your primary
installation anchor.

**Work in Progress:** As the setup script configures your local AI
infrastructure, new tabs will open automatically in your browser. Each tab
contains specific analysis guidelines and diagnostic checks for the service
currently booting. Please return to your terminal to monitor the installation
progress and follow any on-screen prompts.
