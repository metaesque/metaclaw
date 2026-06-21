# searxng: SearXNG

## Overview

SearXNG operates as a proxy, stripping out tracking parameters and aggregating
results from primary engines like Google, Bing, Wikipedia, and DuckDuckGo. This
prevents the OpenClaw node's IP from being quickly fingerprinted or rate-limited
by a single provider.

For OpenClaw agents, SearXNG serves as the primary Retrieval-Augmented
Generation (RAG) backend when Cloud APIs are forbidden. By enforcing local
aggregation, the AI can securely fetch up-to-date real-world context without
leaking queries to third-party corporate APIs.

SearXNG's architecture is highly hackable, allowing the framework to request
`format=json` natively, returning structured data directly to the LLM context
window without requiring heavy, local HTML-to-Markdown processing.

<h2 id="diagnostic-checks">Diagnostic Checks (searcher searxng)</h2>
1. **API Readiness:** You should see `OK`
2. **Status:** You should see `SUCCESS: SearXNG API is actively serving requests.`
