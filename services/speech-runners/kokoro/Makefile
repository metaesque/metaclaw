SERVICE_TITLE = Kokoro Speech Runner
SERVICE_NAME = kokoro-speech-runner
DOCKER_SHELL_CMD = /bin/bash

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Application startup complete

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:$(KOKORO_PORT)/docs >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Kokoro API is unreachable."; exit 1; fi
	@if ! grep -q "200" verification.log; then echo "FATAL: Kokoro returned an unexpected HTTP status."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "200"

clobber-data:
	@echo "[$(SERVICE_TITLE)] No persistent data to clobber."
