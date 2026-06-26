# browseai: Browse AI

## Overview

Browse AI relies on a visual recording interface. A human user performs the
scraping steps once (clicking, selecting data), and the platform generates a
persistent, automated API endpoint for that specific task. It excels at
scheduled execution and detecting changes on a page.

For OpenClaw, Browse AI is exceptionally useful for recurrent monitoring
workflows. Instead of OpenClaw constantly polling a website (which wastes API
tokens and compute power), Browse AI handles the continuous monitoring in the
cloud.

When a specific event occurs—like a price dropping below a threshold or a new
job being posted—Browse AI can trigger a webhook back to the OpenClaw Event
Gateway, waking the agent up only when there is actionable data to process.
