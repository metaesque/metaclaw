# HEARTBEAT.md - Proactive Discovery Loop

Execute this loop once every 12 hours. If no findings pass the strict novelty threshold, reply `HEARTBEAT_OK` to keep the channel clear.

1. **Ingest:** Use `poll_rss_feeds` and `query_arxiv` to gather the last 24 hours of data across the monitored matrices.
2. **Filter:** Discard any item that is a minor version update, a commercial product launch masquerading as research, or a re-reporting of old news.
3. **Score:** Evaluate the remaining items for their potential to disrupt existing paradigms.
4. **Surface:** If an item scores highly, draft a concise brief containing:
   - The core discovery/proof.
   - The underlying mechanism.
   - The theoretical impact on current structural models.
