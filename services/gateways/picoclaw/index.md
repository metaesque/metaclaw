# picoclaw: PicoClaw

## Overview

PicoClaw is an open-source, ultra-lightweight personal AI assistant tailored
specifically for embedded Linux boards and resource-constrained environments.
Written in Go, the gateway boasts a memory footprint of under 10MB and boots in
less than a second. It is distributed as a portable binary across ARM, x86_64,
and RISC-V architectures, making it incredibly easy to deploy on low-cost edge
devices.

Despite its minuscule size, PicoClaw acts as a capable bridge between external
LLM providers (like Anthropic, DeepSeek, or vLLM) and popular messaging
platforms like Telegram and Discord. It supports persistent memory across
sessions and can execute scheduled background tasks via cron jobs, allowing it
to function as a proactive, always-on assistant. While its autonomy is
deliberately limited compared to the full OpenClaw framework, PicoClaw excels at
basic personal automation and monitoring tasks. It is the perfect solution for
users who want to run a reliable, responsive AI chat agent on a cheap Raspberry
Pi tucked away in a closet.
