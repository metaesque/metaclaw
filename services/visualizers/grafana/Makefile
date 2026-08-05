SERVICE_TITLE = Grafana Visualizer Service
SERVICE_NAME = grafana-visualizer
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = HTTP Server Listen

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@docker exec $(SERVICE_NAME) curl -s http://localhost:3000/api/health >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Grafana API is unreachable."; exit 1; fi
	@if ! grep -q '"database":"ok"' verification.log; then echo "FATAL: Grafana database is unhealthy."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log '"database":"ok"'

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Grafana data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/grafana-data

