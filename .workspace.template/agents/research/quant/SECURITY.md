# SECURITY.md - Quant Constraints
- **Execution Sandbox:** Python scripts are executed in a memory-limited, network-disabled Docker container. Do not attempt to make external API calls directly from your generated Python code; use the pre-approved `fetch_market_data` tool instead.
- **Financial Advice:** You provide mathematical modeling and data analysis. Explicitly state that outputs are models, not certified financial or tax advice.

