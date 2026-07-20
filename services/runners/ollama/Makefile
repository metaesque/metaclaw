SERVICE_TITLE = Ollama Runner Service
# Ollama is host-native, not dockerized, so SERVICE_NAME is N/A, but we set it for completeness
SERVICE_NAME = ollama-runner

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

PID_FILE = .ollama.pid
LOG_FILE = ollama.log

.PHONY: up down status clean-state clobber-data check-status check-logs wait-healthy pull-models apply docs

up:: ./bin/ollama
	@if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is already running (PID: $$(cat $(PID_FILE)))" ; \
	else \
		echo "Cleaning up any orphaned processes before boot..." ; \
		$(MAKE) --no-print-directory down ; \
		echo "Starting Ollama natively..." ; \
		mkdir -p $(EXTERNAL_DRIVE_PATH)/ollama-models ; \
		OLLAMA_HOST=$(OLLAMA_HOST):$(OLLAMA_PORT) OLLAMA_VULKAN=1 OLLAMA_IGPU_ENABLE=1 HIP_VISIBLE_DEVICES=-1 OLLAMA_MODELS=$(EXTERNAL_DRIVE_PATH)/ollama-models nohup ./bin/ollama serve > $(LOG_FILE) 2>&1 < /dev/null & \
		echo $$! > $(PID_FILE) ; \
	fi
	@$(MAKE) --no-print-directory pull-models

down::
	@echo "Stopping Ollama..."
	@if [ -f $(PID_FILE) ]; then \
		kill $$(cat $(PID_FILE)) 2>/dev/null || true ; \
		rm -f $(PID_FILE) ; \
	fi
	@ORPHAN=$$(lsof -t -i TCP:$(OLLAMA_PORT) 2>/dev/null) ; \
	if [ -n "$$ORPHAN" ]; then \
		echo "Force killing orphaned process on port $(OLLAMA_PORT) (PID: $$ORPHAN)..." ; \
		kill -9 $$ORPHAN 2>/dev/null || true ; \
	fi

status::
	@if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is RUNNING." ; \
	else \
		echo "Ollama is STOPPED." ; \
	fi

check-logs::
	@echo "[$(SERVICE_TITLE)] Tailing last 5 lines of $(LOG_FILE)..."
	@tail -n 5 $(LOG_FILE) 2>/dev/null || echo "Log file not found."

check-status:: status
	@echo "================================================================================"
	@echo "= $(SERVICE_TITLE) INTEGRITY VERIFICATION"
	@echo "================================================================================"
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Responsiveness ---" > verification.log
	@curl -s http://127.0.0.1:$(OLLAMA_PORT)/api/tags | $(PYTHON_BIN) -c "import sys, json; data=json.load(sys.stdin); print(f'Models Loaded: {len(data.get(\"models\", []))}')" 2>/dev/null >> verification.log || echo "API unreachable." >> verification.log
	@if grep -q "API unreachable" verification.log; then echo "FATAL: Ollama API unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "Models Loaded:"

clean-state:: down
	@echo "Scrubbing local runtime state..."
	@rm -f $(LOG_FILE) $(PID_FILE) verification.log index.html .updated

clobber-data:
	@if [ -n "$(EXTERNAL_DRIVE_PATH)" ]; then \
		echo "Purging Ollama models from external drive..." ; \
		rm -rf $(EXTERNAL_DRIVE_PATH)/ollama-models ; \
	fi

# Root reconciliation integration
apply:: .env
	@echo "[$(SERVICE_TITLE)] Reconciling state..."
	@chmod +x install.sh
	@rm -f .updated
	@./install.sh
	@echo "[$(SERVICE_TITLE)] Bouncing daemon to apply new configuration..."
	@$(MAKE) --no-print-directory down
	@rm -f .updated
	@$(MAKE) --no-print-directory up

./bin/ollama:
	@echo "Downloading Ollama binary via install.sh..."
	@mkdir -p ./bin
	@chmod +x install.sh
	@./install.sh

wait-healthy:: status
	@echo "[$(SERVICE_TITLE)] Awaiting healthy state..."
	@attempt=1; \
	while [ $$attempt -le 30 ]; do \
		if curl -s http://127.0.0.1:$(OLLAMA_PORT)/api/tags > /dev/null; then \
			echo "[$(SERVICE_TITLE)] Status: HEALTHY."; \
			exit 0; \
		fi; \
		echo "[$(SERVICE_TITLE)] Status: starting. Retrying in 2s ($$attempt/30)..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	echo "FATAL: [$(SERVICE_TITLE)] Failed to reach healthy state."; \
	cat $(LOG_FILE) 2>/dev/null || true; \
	exit 1

# Instructs the running Ollama process to pull any models assigned to it by the global orchestrator configuration
pull-models: wait-healthy
	@echo "[$(SERVICE_TITLE)] Validating and pulling assigned local models..."
	@for raw_model in $(OLLAMA_TARGET_MODELS) $(OPENCLAW_JUDGE_MODEL); do \
		if echo "$$raw_model" | grep -q "^ollama/"; then \
			clean_model=$$(echo "$$raw_model" | sed 's/ollama\///'); \
			echo "  -> Pulling $$clean_model (This may take several minutes)..."; \
			OLLAMA_HOST=$(OLLAMA_HOST):$(OLLAMA_PORT) OLLAMA_MODELS=$(EXTERNAL_DRIVE_PATH)/ollama-models ./bin/ollama pull $$clean_model || echo "\nWARNING: Failed to pull $$clean_model."; \
		fi; \
	done
