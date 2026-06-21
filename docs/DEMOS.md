# MetaClaw Demonstration Gallery

This document catalogs example scripts and Agents designed to demonstrate the utility of MetaClaw's complex service architecture to non-technical users.

## 1. Competitor Intelligence Demo

**Location:** `bin/demos/competitor_research.py`

**Purpose:** 
Demonstrates the handoff between the three distinct external interaction services (Searchers, Fetchers, and Browsers) using the Tier 0 providers. 

**The Workflow:**
The user asks the agent to find competing software products to "Notion" and determine the cost of their lowest paid tier.

1. **Step 1: The Searcher (`searxng`)** 
   * **Action:** The script simulates querying the SearXNG proxy to find recent articles and links discussing "Notion alternatives."
   * **Value:** Shows how the AI discovers *where* information lives without directly executing corporate API calls (like Google Search) that cost money or track users.
2. **Step 2: The Fetcher (`crawl4ai`)**
   * **Action:** The script simulates passing one of the discovered URLs into Crawl4AI.
   * **Value:** Shows how the Fetcher rapidly grabs the content and strips away ads, navbars, and noise, returning clean Markdown so the AI doesn't waste tokens reading raw HTML tags.
3. **Step 3: The Browser (`browseruse`)**
   * **Action:** Pricing pages are notoriously difficult to scrape because they require interaction (e.g., clicking a toggle switch from "Annually" to "Monthly"). The script simulates Browser Use driving a real Chromium instance to physically click the toggle and extract the exact price.
   * **Value:** Highlights that while Fetchers "read," Browsers "act," providing human-like resilience for complex web workflows.