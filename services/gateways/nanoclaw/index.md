# nanoclaw: NanoClaw

## Overview

NanoClaw is a radically minimalist successor to the OpenClaw framework,
distilling the concept of an autonomous AI agent into a single process managed
by just five core files. Rather than relying on a sprawling microservice
architecture, it is designed for users who want maximum simplicity and
auditability. The entire codebase is small enough for a single developer to read
and understand in an afternoon, making it highly customizable.

Security in NanoClaw is handled at the operating system level rather than the
application level. It isolates agents inside Apple Containers (on macOS) or
Docker containers (on Linux), meaning the agent can only interact with
explicitly mounted directories. This provides a robust defense against rogue AI
actions, ensuring that bash commands executed by the agent never touch the host
system.

Despite its minimalist footprint, NanoClaw retains powerful core capabilities,
including a built-in task scheduler, multi-agent swarms, and a native WhatsApp
interface for mobile control. It is the ideal gateway for privacy-conscious
tinkerers who want to run a capable, secure AI assistant on a Raspberry Pi
without the overhead of enterprise-grade orchestration tools.
