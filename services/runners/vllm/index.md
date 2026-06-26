# vllm: vLLM

## Overview

vLLM is a high-throughput, memory-efficient serving engine designed specifically
for large language models. Its core innovation is PagedAttention, an algorithm
that manages attention keys and values like an operating system manages virtual
memory. This prevents memory fragmentation and allows the engine to batch
significantly more requests concurrently than standard inference engines.

Because it is engineered primarily for datacenter environments and production
deployments, vLLM relies heavily on powerful, dedicated GPUs (typically Nvidia).
It is not designed to run efficiently on consumer laptops with unified memory or
pure CPUs, but rather to maximize the tokens-per-second throughput of enterprise
hardware.

For OpenClaw, vLLM is the premier choice when deploying an OpenClaw node on a
dedicated cloud VPS or a high-end local workstation. Since vLLM natively exposes
an OpenAI-compatible API server, OpenClaw can connect to it seamlessly. Its
massive throughput is particularly useful when OpenClaw spawns multiple
concurrent sub-agents, as vLLM can handle the simultaneous prompt evaluations
without bottlenecking.
