# Feature Architecture Decision Records (ADRs)

This document captures the historical context, rejected alternatives, and ultimate justifications for the architectural standards enforced within the MetaClaw `features/` subsystem.

## ADR 1: The "Features" Abstraction Layer

**Context:**
As MetaClaw evolved, diverse functionalities like Kasa smart plug monitoring and distributed AutoFS storage meshing were initially baked directly into root orchestration scripts and generic library files. This threatened to create a tightly coupled monolith.

**Alternatives Considered:**

1.  **Monolithic Core:**
    *   *Pros:* Easiest to rapidly prototype.
    *   *Cons:* Unmaintainable. Changes to power monitoring could inadvertently break storage setup routines.
2.  **Strict Microservices:**
    *   *Pros:* Complete isolation.
    *   *Cons:* Overkill for local network configurations (like NFS exports) which require tight integration with host OS tools.
3.  **Modular Feature Directories (`./features/<name>`):**
    *   *Pros:* Encapsulates setup logic, documentation, and feature-specific constants while still utilizing the shared `lib/` and global Makefiles.

**Decision:**
We enforce the **Modular Feature Directories** approach.

**Justification:**
This strikes the perfect balance. It provides a formalized boundary for documentation (`docs/DESIGN.md`) and initialization logic (`bin/<name>_setup.py`), while recognizing that these are holistic platform capabilities, not isolated containerized services.

## ADR 2: Omission of AGENTS.md in Features

**Context:**
The `projects/` workspace relies heavily on `AGENTS.md` to impose strict rules on autonomous LLMs modifying the code. We evaluated whether `features/` needed the same.

**Decision:**
Do not require `AGENTS.md` for Features.

**Justification:**
Projects are discrete, self-contained units of work intentionally sandboxed for LLMs. Features are cross-cutting platform infrastructure. While LLMs assist in building features, the governance of a feature is inherently system-wide and better served by human-readable `DESIGN.md` and `DECISIONS.md` files.
