# HEARTBEAT.md - Proactive Checks

Run these checks periodically (every 4-6 hours during the workday). If nothing needs attention, reply `HEARTBEAT_OK` to keep the logs clean.

1. **Stale Tickets:** Execute the `flag_stale_tickets` tool to check for any tickets in the "In Progress" column that haven't been updated in >48 hours. If found, draft a polite status request to the assignee.
2. **Blockers:** Scan recent chat history or ticket comments for the words "blocked", "stuck", or "waiting on". Surface these immediately in a concise summary.
3. **Sprint Scope Creep:** Identify if any new scope (tickets added to the current sprint) was introduced without an associated point estimation.
4. **Sign-off Sweep:** Check the task tracker for any items marked "Ready for Review" or "Awaiting Sign-off". Verify the deliverable meets the acceptance criteria documented in the original ticket.
