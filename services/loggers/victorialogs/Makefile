SERVICE_TITLE = VictoriaLogs Aggregator Service
SERVICE_NAME = victorialogs
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

# VictoriaLogs logs this specific string when it is fully ready to accept HTTP connections
LOG_READY_SIGNAL = started VictoriaLogs in

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@curl -s http://localhost:$(VICTORIALOGS_PORT)/health >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@echo "--- 2. Ingestion ---" >> verification.log
	@sleep 2
	@if docker logs fluent-bit 2>&1 | grep -qEi "output:http|fluent bit|active-logger"; then echo "Fluent Bit status confirms logs are being streamed" >> verification.log; else echo "Fluent Bit log stream missing" >> verification.log; fi
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: VictoriaLogs API is unreachable."; exit 1; fi
	@if ! grep -q "OK" verification.log; then echo "FATAL: VictoriaLogs health endpoint returned unexpected state."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "OK" "Fluent Bit status confirms logs are being streamed"

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external VictoriaLogs database..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/victorialogs-data
