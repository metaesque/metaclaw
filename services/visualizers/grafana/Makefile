SERVICE_TITLE = Grafana Visualization Service
SERVICE_NAME = grafana
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = HTTP Server Listen

pre-up:
	@echo "[$(SERVICE_TITLE)] Ensuring external data directory permissions..."
	@if [ -n "$(EXTERNAL_DRIVE_PATH)" ]; then \
		mkdir -p $(EXTERNAL_DRIVE_PATH)/grafana-data; \
		docker run --rm -v $(EXTERNAL_DRIVE_PATH)/grafana-data:/mnt alpine chown -R 472:0 /mnt 2>/dev/null || true; \
	fi

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Dashboard Health ---" > verification.log
	@curl -s -I http://localhost:$(GRAFANA_PORT)/login >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Grafana failed to serve UI."; exit 1; fi
	@if ! grep -q "200 OK" verification.log; then echo "WARNING: Grafana endpoint did not return HTTP 200."; fi
	@echo "SUCCESS: Grafana dashboard is reachable." >> verification.log
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Grafana dashboard is reachable."

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Grafana data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/grafana-data
