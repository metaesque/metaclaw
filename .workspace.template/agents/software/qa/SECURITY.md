# SECURITY.md - QA Constraints
- **Execution Scope:** You may only execute shell commands related to test runners (e.g., `pytest`, `npm test`). You may not compile production binaries.
- **Database Access:** You must only connect to the isolated `test_db`. Never run tests against production or staging databases.

