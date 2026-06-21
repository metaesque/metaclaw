# docker: Docker

## Overview

Docker is the industry-standard platform for developing, shipping, and running
applications in lightweight containers. It isolates processes using Linux kernel
features like namespaces and cgroups, ensuring that applications run
consistently regardless of the host environment. Its ubiquitous adoption and
massive ecosystem make it the default deployment mechanism for almost all modern
microservices.

However, standard Docker is fundamentally flawed as a security sandbox for
executing untrusted, LLM-generated code. Because Docker containers share the
host operating system's kernel, a sophisticated exploit or a hallucinated
command (such as attempting to modify kernel modules or escaping the container
privileges) can directly compromise the host machine.

In the context of OpenClaw, Docker is exceptional for packaging the framework's
core services (like the Gateway, Proxy, and Database). But when the OpenClaw
agent utilizes a code interpreter tool to run arbitrary Python or Bash scripts,
standard Docker boundaries are insufficient. Relying solely on Docker for agent
sandboxing exposes the user's host machine to unacceptable risk from both
malicious prompt injections and erratic AI behavior.
