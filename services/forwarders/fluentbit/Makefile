SERVICE_TITLE = Fluent Bit Forwarder Service
SERVICE_NAME = fluent-bit
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

# The default fluent-bit image does not output a ready signal easily greppable without debug logs,
# so we rely on the native container state for baseline checks.
LOG_READY_SIGNAL = Fluent Bit

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Forwarder Health ---" > verification.log
	@if [ "$$(docker inspect --format '{{.State.Status}}' $(SERVICE_NAME))" = "running" ]; then echo "SUCCESS: Fluent Bit is running." >> verification.log; else echo "CONNECTION_FAILED" >> verification.log; fi
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Fluent Bit failed to start."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Fluent Bit is running."

clobber-data:
	@echo "[$(SERVICE_TITLE)] No local data to clobber."
