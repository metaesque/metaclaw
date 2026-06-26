# manifest: Manifest

## Overview

Manifest is an open-source LLM router and AI proxy built specifically with AI
agents and complex orchestration workflows in mind. It acts as an intermediary
layer that not only translates API requests but actively scores and routes them
based on a sophisticated multi-dimensional algorithm. Manifest is designed to
optimize interactions by determining the most cost-effective and capable model
for any given prompt in real-time, aiming to drastically reduce API costs.

A distinguishing feature of Manifest is its focus on agentic behavior,
specifically addressing issues like "tier oscillation" during multi-turn
conversations. It uses intelligent session management to group related requests,
ensuring that an agent maintains contextual continuity and doesn't bounce
between vastly different model tiers mid-task. Furthermore, it records deep
telemetry and observability metrics natively formatted as agent messages, making
it easier to track autonomous systems.

Within the OpenClaw ecosystem, Manifest acts as a highly specialized, native-
feeling gateway. Because it was explicitly built with agentic frameworks in
mind, it excels at managing the heavy, multi-turn, tool-calling workloads that
OpenClaw generates. By utilizing Manifest, an OpenClaw deployment can
intelligently route simple file-reading tasks to a cheap, fast model, while
automatically escalating complex coding or reasoning tasks to a premium model,
all while keeping the session stable and costs minimized.
