# memori: Memori Labs

## Overview

Memory-as-a-Service platforms (like Mem0, often associated with Memori concepts)
provide an intelligent, API-driven memory layer specifically built for Large
Language Models. Instead of just storing raw text or vectors, these platforms
actively extract entities, facts, and user preferences from conversations. They
handle the synthesis, deduplication, and decay of information automatically.

In the context of OpenClaw, this technology shifts the burden of memory curation
away from the agent's raw compute. Instead of the agent manually reading and
writing to `MEMORY.md`, it passes the conversational transcript to the memory
API. The service automatically extracts insights (e.g., "Wade is living in Costa
Rica in 2024") and structures them into a queryable graph.

This provides OpenClaw agents with highly synthesized real-time memory. When
generating a response, the agent queries the API and receives a curated, highly
relevant set of facts tailored to the exact prompt, drastically reducing token
usage and eliminating the need for the agent to manually sift through years of
disorganized markdown files.
