# Changelog

## 2026.07.28
- **Fixed:** `sre_sysadmin` agent crash by adding `execute_shell_command` to its allowed tools list.
- **Changed:** Restored explicit double quotes around `OLLAMA_TARGET_MODELS` in `bin/orchestrate.py` to support safe `source .env` execution while maintaining Make loop compatibility.
- **Changed:** Refactored `install.sh` to safely extract Ollama binaries to isolated directories, protecting `lib/metaclaw.py` from catastrophic overwrite.
- **Added:** Teardown logic in `install.sh` to destroy conflicting global `/usr/local/bin/ollama` installations.
- **Added:** Custom Modelfile generation (`metaclaw-llama4-scout`) to strictly enforce Llama 4 `<|start_header_id|>` boundaries, successfully suppressing the `assistant\n\n` generation leak.
