# MetaClaw Architectural Tiers

A Tier represents a discrete stage in the growth of your overall local cluster. It dictates the scale of hardware deployed across the planes.

## Tier 0: The Day 1 Minilith {#tier-0}

* **Setup**: The entire cluster consists of a single, dual-use laptop. RAM is
  strictly budgeted (6GB-8GB). The framework uses lightweight alternatives
  (SQLite instead of Postgres, LiteLLM routing to Cloud APIs for heavy
  reasoning, Ollama strictly for local text embeddings).
* **Benefit**: Zero financial cost to validate the framework's utility before
  purchasing dedicated hardware.

## Tier 1: The Month 2 Monolith {#tier-1}

* **Setup**: The cluster transitions to a single, dedicated machine. All four
  Planes run on this one Control Node. Heavy services are rate-limited via
  Docker to prevent crashes. The Compute Plane remains outsourced to Cloud APIs.
* **Benefit**: True 24/7 autonomous operation with robust relational memory and
  background web scraping.

## Tier 2: Data Sovereignty {#tier-2}

* **Setup**: The cluster expands to two machines. The Compute Plane is migrated
  off the Monolith and onto a dedicated inference node. The Control node manages
  routing, execution, and archiving, while delegating heavy reasoning to the
  Compute node.
* **Benefit**: Absolute data privacy and zero recurring API costs. Infinite
  agent loops can run overnight without accumulating massive bills.

## Tier 3E: Sandbox Extraction {#tier-3e}

* **Setup**: The cluster expands to three machines. The Execution Plane is
  migrated off the Control Node and onto a dedicated Sandbox Node. The Control
  Node continues to host the Archive Plane.
* **Benefit**: Safe execution of highly volatile workloads. Hallucinated code or
  memory-leaking browsers will not crash the core Gateway or corrupt the
  databases.

## Tier 3A: Archive Extraction {#tier-3a}

* **Setup**: The cluster expands to three machines. The Archive Plane is
  migrated off the Control Node onto a dedicated Context Node. The Control Node
  continues to host the Execution Plane.
* **Benefit**: SRE-grade stability with near-infinite, lightning-fast semantic
  recall, keeping databases completely isolated from gateway traffic spikes.

## Tier 4: The Distributed Farm {#tier-4}

* **Setup**: The cluster expands to four or more machines. Every Plane is
  physically isolated onto its own dedicated hardware. The original Month 2
  Monolith is now stripped of heavy workloads, running strictly as the Control
  Plane.
* **Benefit**: Absolute enterprise-grade architecture. No single node failure
  can cascade and destroy the entire agent ecosystem.
