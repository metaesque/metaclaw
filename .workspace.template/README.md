# OpenClaw Workspace

This is your persistent workspace directory. It exists securely outside of the MetaClaw Git repository to ensure your personal agents, configurations, and memory transcripts are never accidentally deleted during an infrastructure reset.

## Structure
- `agents/`: Contains your YAML agent definitions.
- `tools/`: Contains your custom TypeScript or Python tools.
- `memory/`: (Generated at runtime) Holds transcript history and vector summaries.

**Configuration as Code:**
If you wish to create a permanent agent that survives GUI resets, create a new YAML file within the `agents/` directory rather than relying solely on the Web UI.
