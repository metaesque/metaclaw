# HEARTBEAT.md - Proactive Checks

1. **Daily Cost Sweep:** Analyze the LiteLLM telemetry logs for the last 24 hours. If total API spend exceeds $5.00 USD, immediately generate an alert summarizing which agent/model caused the spike.
2. **Dependency Audit:** Run `scan_vulnerabilities`. Flag any 'High' or 'Critical' CVEs immediately.
