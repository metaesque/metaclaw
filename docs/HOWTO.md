# MetaClaw How-To

## Managing Cluster State
Always use the top-level Make targets to deploy changes:
```bash
make apply
```

## Debugging Tool Calls
If an agent fails to call a tool, check the LiteLLM proxy logs first:
```bash
docker logs litellm-proxy | grep -A 20 "litellm.acompletion"
```
If the tool call outputs as raw text (e.g., `<tool_calls>...</tool_calls>`), the model template or LiteLLM middleware requires adjustment.

## Adding Agent Tools
If an agent crashes with `No callable tools remain after resolving explicit tool allowlist`, edit its configuration file in `config/agents/<agent_name>.yaml` and add the required tool to the `tools.allow` list.
