# crawl4ai: Crawl4AI

## Overview

Crawl4AI simplifies the RAG ingestion pipeline by rendering JavaScript-heavy
pages via an internal browser, executing dynamic interaction hooks (like 'Load
More'), and converting the DOM directly into optimized Markdown.

Unlike rigid scraping tools, it integrates LLM-based extraction directly into
the crawling loop, allowing you to pass an extraction schema or query string.
The crawler filters out navbar, footer, and ad noise automatically using
advanced pruning heuristics.

For OpenClaw, running Crawl4AI locally ensures that heavy scraping tasks are
isolated and parallelized. It bypasses the need for external API subscriptions
while providing deep control over caching, proxies, and session management.

<h2 id="diagnostic-checks">Diagnostic Checks (fetcher crawl4ai)</h2>
1. **API Readiness:** You should see a JSON response containing `"status":"healthy"` followed by `SUCCESS: Crawl4AI API is actively serving requests.`
