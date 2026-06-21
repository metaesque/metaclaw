# tavily: Tavily

## Overview

Traditional search APIs return raw HTML pages or brief meta-descriptions,
forcing the AI agent to waste thousands of tokens reading irrelevant boilerplate
to find a single fact. Tavily solves this by performing the extraction and
synthesis on its own servers, returning clean, LLM-ready context.

When integrated into OpenClaw, Tavily acts as an extreme optimization layer. If
the agent needs to know 'Who won the election yesterday?', Tavily doesn't just
hand the agent five news URLs to read; it hands the agent the exact answer
synthesized from those five URLs.

This drastically reduces context bloat, lowers API costs, and minimizes the risk
of hallucinations, making it an exceptional choice for users running OpenClaw on
constrained hardware where local compute is precious.
