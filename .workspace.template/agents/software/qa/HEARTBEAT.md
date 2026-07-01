# HEARTBEAT.md - Proactive Checks

1. **Nightly Builds:** If this heartbeat fires between 00:00 and 04:00, execute the full integration test suite against the `staging` branch.
2. **Coverage Drop Check:** Analyze the latest test coverage report. Flag any modules that have dropped below 85% coverage.
