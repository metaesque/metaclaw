SERVICE_TITLE = Node Exporter Service
SERVICE_NAME = node-exporter
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Listening on

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Exporter Health ---" > verification.log
	@curl -s http://localhost:$(NODE_EXPORTER_PORT)/metrics | grep -m 1 "node_cpu_seconds_total" >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Node Exporter failed to serve metrics."; exit 1; fi
	@echo "SUCCESS: Node Exporter is serving metrics." >> verification.log
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Node Exporter is serving metrics."

clobber-data:
	@echo "[$(SERVICE_TITLE)] No persistent data to clobber."
