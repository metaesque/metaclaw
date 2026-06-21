# linkup: Linkup

## Overview

Linkup is designed to ground Large Language Models in hard facts. It prioritizes
premium, verified content sources over general web chatter, making it highly
reliable for professional, financial, or strategic queries. It features a dual-
tier system: a 'Standard' mode for blazing-fast RAG grounding, and a 'Deep' mode
for complex, chain-of-thought information retrieval.

For OpenClaw, Linkup acts as the ultimate business intelligence integration.
When an agent is tasked with generating a macro-risk analysis on a competitor,
Linkup's Deep mode will autonomously execute multiple sub-searches and
synthesize the findings before returning the payload to OpenClaw.

It also features robust built-in security, including managed authentication and
strict access controls. This means you don't have to hardcode sensitive API keys
directly into your OpenClaw agent logic, making it ideal for corporate or multi-
user environments.
