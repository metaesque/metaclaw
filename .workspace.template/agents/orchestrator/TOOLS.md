# TOOLS.md - Orchestrator Notes

## Delegation Syntax
When delegating, you must use your provided `delegate` tool.
Always provide the sub-agent with *exhaustive* context. They do not share your memory. They do not know what the user asked you. You must summarize the entire goal and their specific required output format in the delegation payload.
