# firecrawl: Firecrawl

## Overview

Firecrawl simplifies the complex pipeline of moving data from a raw website into
an AI agent's context window. It handles all the heavy lifting behind the
scenes, including rotating proxies, managing rate limits, rendering JavaScript-
heavy pages, and bypassing aggressive anti-bot protections.

For OpenClaw, Firecrawl acts as a massive upgrade to the default `web_fetch`
tool. Instead of just grabbing raw HTML, it returns perfectly formatted Markdown
that maximizes token efficiency. Furthermore, it supports interactive
scraping—meaning OpenClaw can instruct Firecrawl to scroll, wait, or click a
button before extracting the data.

This provider is highly versatile because it can be consumed as a managed cloud
API (for low-resource machines) or fully self-hosted via Docker for users with
the hardware to support its concurrent worker queues.
