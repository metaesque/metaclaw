SERVICE_TITLE = Ollama Runner Service
# Ollama is host-native, not dockerized, so SERVICE_NAME is N/A, but we set it for completeness
SERVICE_NAME = ollama-runner

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

-include $(FRAMEWORK_ROOT)/.env
-include .env
# ARCHITECTURAL SHIFT: Depend on the abstracted gateway symlink instead of hardcoding openclaw-gateway
-include $(FRAMEWORK_ROOT)/services/gateway/.env
export

PYTHON_BIN ?= python3

PID_FILE = .ollama.pid
LOG_FILE = ollama.log

# Strips the Litellm provider prefix (e.g., 'ollama/') to isolate the native model name
JUDGE_MODEL_CLEAN = $(shell echo $(OPENCLAW_JUDGE_MODEL) | sed 's/ollama\///')

.PHONY: up down status clean-state clobber-data check-status check-logs wait-healthy pull-judge apply docs

docs: | $(PYTHON_BIN)
	@if [ -f index.md ]; then \
		echo "[$(SERVICE_TITLE)] Compiling markdown documentation..."; \
		$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/compile_md.py -i index.md --html; \
	fi

.env: .env.template $(wildcard .env.json)
	@echo "Instantiating .env for $(SERVICE_TITLE)..."
	$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/env_instantiate.py $(if $(filter down clean-state clobber-data,$(MAKECMDGOALS)),--teardown)

up: .env ./bin/ollama docs
	@if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is already running (PID: $$(cat $(PID_FILE)))" ; \
	else \
		echo "Cleaning up any orphaned processes before boot..." ; \
		$(MAKE) --no-print-directory down ; \
		echo "Starting Ollama natively..." ; \
		OLLAMA_HOST=127.0.0.1:$(OLLAMA_PORT) OLLAMA_MODELS=$(EXTERNAL_DRIVE_PATH)/ollama-models ./bin/ollama serve > $(LOG_FILE) 2>&1 & \
		echo $$! > $(PID_FILE) ; \
	fi
	@$(MAKE) --no-print-directory pull-judge

down:
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

status:
	@if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is RUNNING." ; \
	else \
		echo "Ollama is STOPPED." ; \
	fi

check-logs:
	@echo "[$(SERVICE_TITLE)] Tailing last 5 lines of $(LOG_FILE)..."
	@tail -n 5 $(LOG_FILE) 2>/dev/null || echo "Log file not found."

check-status: status
	@echo "================================================================================"
	@echo "= $(SERVICE_TITLE) INTEGRITY VERIFICATION"
	@echo "================================================================================"
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Responsiveness ---" > verification.log
	@curl -s http://127.0.0.1:$(OLLAMA_PORT)/api/tags | $(PYTHON_BIN) -c "import sys, json; data=json.load(sys.stdin); print(f'Models Loaded: {len(data.get(\"models\", []))}')" >> verification.log || echo "API unreachable." >> verification.log
	@if grep -q "API unreachable" verification.log; then echo "FATAL: Ollama API unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "Models Loaded:"

clean-state: down
	@echo "Scrubbing local runtime state..."
	@rm -f $(LOG_FILE) $(PID_FILE) verification.log index.html .updated

clobber-data:
	@if [ -n "$(EXTERNAL_DRIVE_PATH)" ]; then \
		echo "Purging Ollama models from external drive..." ; \
		rm -rf $(EXTERNAL_DRIVE_PATH)/ollama-models ; \
	fi

# Root reconciliation integration
apply: .env
	@echo "[$(SERVICE_TITLE)] Reconciling state..."
	@chmod +x install.sh
	@rm -f .updated
	@./install.sh
	@if [ -f .updated ]; then \
		echo "[$(SERVICE_TITLE)] Binary updated. Bouncing daemon..."; \
		$(MAKE) --no-print-directory down; \
		$(MAKE) --no-print-directory up; \
		rm -f .updated; \
	fi

./bin/ollama:
	@echo "Downloading Ollama binary via install.sh..."
	@mkdir -p ./bin
	@chmod +x install.sh
	@./install.sh

wait-healthy: status
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

# Instructs the running Ollama process to pull the specific weights defined in your Gateway config
pull-judge: wait-healthy
	@if [ -z "$(JUDGE_MODEL_CLEAN)" ]; then \
		echo "WARNING: OPENCLAW_JUDGE_MODEL is undefined (Gateway .env not instantiated?). Skipping judge pull."; \
	else \
		echo "Pulling local judge model ($(JUDGE_MODEL_CLEAN))..."; \
		OLLAMA_HOST=127.0.0.1:$(OLLAMA_PORT) OLLAMA_MODELS=$(EXTERNAL_DRIVE_PATH)/ollama-models ./bin/ollama pull $(JUDGE_MODEL_CLEAN) || { echo "\nWARNING: Failed to pull $(JUDGE_MODEL_CLEAN). TLS error detected (SecPolicyCreateSSL). The OpenClaw Gateway will gracefully fallback to the cloud 'medium-model'."; exit 0; }; \
	fi
