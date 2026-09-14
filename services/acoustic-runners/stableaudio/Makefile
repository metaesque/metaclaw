SERVICE_TITLE = Stable Audio Acoustic Runner
SERVICE_NAME = stableaudio-acoustic-runner
DOCKER_SHELL_CMD = /bin/bash

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

COMPOSE_FILE := $(STABLEAUDIO_COMPOSE_FILE)
export COMPOSE_FILE

LOG_READY_SIGNAL = Serving on

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:$(STABLEAUDIO_PORT)/ >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Stable Audio API is unreachable."; exit 1; fi
	@if ! grep -q "200" verification.log; then echo "FATAL: Stable Audio returned an unexpected HTTP status."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "200"

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Stable Audio data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/stableaudio-models
