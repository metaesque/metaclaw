SERVICE_TITLE = Browser Use Service
SERVICE_NAME = browseruse
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Uvicorn running on

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Health Check ---" > verification.log
	@curl -s http://localhost:$(BROWSERUSE_PORT)/health >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@cat verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Browser Use API unreachable."; exit 1; fi
	@echo "SUCCESS: Browser Use REST API is actively serving requests."

clean-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Browser Use session data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/browseruse-data
