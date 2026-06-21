# agentbrowser: Agent Browser

## Overview

Standard web pages contain massive amounts of hidden code, styling, and tracking
scripts that overwhelm an AI's context window, leading to high API costs and
hallucinated mistakes. Agent Browser strips away all this noise, generating a
highly compressed 'accessibility tree' that only shows the AI the elements it
can actually interact with, assigning each a simple ID tag like `@e1`.

For OpenClaw, this means the agent doesn't need to write complex programming
logic to interact with a page. It simply looks at the clean snapshot and issues
a basic command like `click @e1`.

Because it runs as a native application rather than a heavy Node.js environment,
it boasts sub-millisecond execution times. This allows OpenClaw to maintain
lightning-fast browsing speeds even on severely hardware-constrained laptops or
Raspberry Pis.
