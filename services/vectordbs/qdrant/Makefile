SERVICE_TITLE = Qdrant Vector Database
SERVICE_NAME = qdrant-vectordb
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Access web UI at

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@curl -s http://localhost:$(QDRANT_PORT_HTTP)/healthz >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Qdrant API is unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "ok" "healthz"

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Qdrant data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/qdrant-data
