# exa: Exa

## Overview

Standard search engines match the literal words in your query to words on a
webpage. Exa uses advanced embedding models to understand the *intent* behind
the query. If an agent searches for 'best practices for scaling postgres', Exa
finds articles that discuss the concept, even if they never use those exact
words, resulting in vastly higher-quality results.

Within OpenClaw, Exa's most powerful feature is 'Highlights'. Instead of
returning the full text of a massive webpage, Exa intelligently extracts only
the few sentences that directly answer the agent's prompt. This cuts token usage
by over 50% per search.

Exa also maintains dedicated, specialized indexes for specific domains like
coding documentation, company data, and people. This allows a specialized
OpenClaw sub-agent (like a coding assistant) to restrict its search purely to
verified GitHub repos and API docs, completely eliminating hallucinated code.
