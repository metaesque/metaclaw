# octoparse: Octoparse

## Overview

Originally built as a visual desktop tool for human researchers, Octoparse
allows users to 'point and click' to create scraping templates. Its cloud
platform can then execute these templates programmatically, handling complex
tasks like infinite scrolling, dropdown menus, and batch URL processing.

Within the OpenClaw framework, Octoparse is best utilized for massive,
structured data harvesting rather than ad-hoc, single-page reads. An OpenClaw
agent can trigger a predefined Octoparse task via API to scrape an entire
catalog of products.

Octoparse handles the cloud execution, IP rotation, and parsing, eventually
returning a clean CSV or JSON dataset to the agent. This cleanly separates the
heavy lifting of batch scraping from the agent's real-time reasoning loop.
