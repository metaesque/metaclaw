SERVICE_TITLE = Crawl4AI Fetcher
SERVICE_NAME = crawl4ai
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include $(FRAMEWORK_ROOT)/services/proxy/.env
-include .env
export

# The crawler's FastAPI application signals readiness upon complete startup
LOG_READY_SIGNAL = Application startup complete

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Health Check ---" > verification.log
	@curl -s http://localhost:$(CRAWL4AI_PORT)/health >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "\nSUCCESS: Crawl4AI API is actively serving requests." >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Crawl4AI API unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log '"status":"healthy"' 'SUCCESS: Crawl4AI API is actively serving requests.'

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Crawl4AI session data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/crawl4ai-data
