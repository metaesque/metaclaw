SERVICE_TITLE = VictoriaMetrics TSDB Service
SERVICE_NAME = victoriametrics-tsdb
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = started VictoriaMetrics in

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@curl -s http://localhost:$(VICTORIAMETRICS_PORT)/health >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: VictoriaMetrics API is unreachable."; exit 1; fi
	@if ! grep -q "OK" verification.log; then echo "FATAL: VictoriaMetrics health endpoint returned unexpected state."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "OK"

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external VictoriaMetrics database..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/victoriametrics-tsdb-data

