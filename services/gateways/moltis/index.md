# moltis: Moltis

## Overview

Moltis is a personal AI assistant built entirely in Rust, focusing on providing
a secure, local-first environment with zero runtime dependencies. It compiles
the entire assistant stack—including the web UI, model routing, memory, and tool
execution—into a single 60MB executable. This architecture eliminates the
overhead of Node.js or Python environments, resulting in an exceptionally fast
and resource-efficient gateway.

The platform excels at secure automation and execution. Every command and
browsing task initiated by Moltis runs within a sandboxed container (Docker,
Podman, or Apple Container) and requires explicit human-in-the-loop approval for
sensitive actions. It includes robust defenses against Server-Side Request
Forgery (SSRF) and supports modern authentication methods like passkeys,
ensuring that the assistant remains strictly under the user's control.

Moltis offers deep integration with both local and cloud models, featuring
built-in Hugging Face downloads and MLX support for accelerated Apple Silicon
inference. With hybrid vector and full-text long-term memory, parallel tool
execution, and multi-channel access via Telegram and a Web UI, it serves as a
powerful, low-level automation hub for developers who prioritize security and
performance.
