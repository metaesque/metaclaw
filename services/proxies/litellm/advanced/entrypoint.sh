#!/bin/sh
set -e

# This wrapper ensures the target application takes over PID 1 via 'exec',
# allowing proper handling of SIGTERM and SIGINT for graceful shutdowns.
if [ "$USE_MONKEY_PATCH" = "true" ]; then
  echo "[INIT] USE_MONKEY_PATCH is true. Booting via Python interception layer..."
  exec python /app/advanced/patch_entrypoint.py "$@"
else
  echo "[INIT] Standard execution. Booting native LiteLLM..."
  exec litellm "$@"
fi
