# llamacpp: llama.cpp

## Overview

llama.cpp is a pure C/C++ inference engine that fundamentally revolutionized the
local AI scene by enabling large language models to run on consumer hardware
without massive dependencies. It pioneered the GGUF file format, which stores
heavily quantized (compressed) model weights that can fit into standard system
RAM or VRAM.

The technology is highly optimized for a wide variety of hardware architectures,
featuring advanced Apple Silicon (Metal) support, AVX instructions for CPUs, and
CUDA for Nvidia GPUs. It operates close to the metal with minimal overhead,
functioning primarily as a command-line tool but including a lightweight HTTP
server.

Within OpenClaw, llama.cpp serves as the foundational bedrock for edge
computing. If an OpenClaw node is deployed on a Raspberry Pi, an older Mac, or
an embedded device, running the native llama.cpp server provides the most
resource-efficient way to host a local model. OpenClaw can target its built-in
server directly, ensuring that even low-powered hardware can provide an active
intelligence layer.
