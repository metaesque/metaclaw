SERVICE_TITLE = Telegraf Collector Service
SERVICE_NAME = telegraf-collector
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Starting Telegraf

# WHAT THIS DOES: Tells the orchestrator to restart the container if the main config or the Kasa feature drop-ins change.
RESTART_DEPS = telegraf.conf $(wildcard $(FRAMEWORK_ROOT)/features/kasa/assets/collectors/telegraf/*.conf)

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Collector Health ---" > verification.log
	@if [ "$$(docker inspect --format '{{.State.Status}}' $(SERVICE_NAME))" = "running" ]; then echo "SUCCESS: Telegraf is running." >> verification.log; else echo "CONNECTION_FAILED" >> verification.log; fi
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Telegraf failed to start."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Telegraf is running."

clobber-data:
	@echo "[$(SERVICE_TITLE)] No persistent data to clobber."
