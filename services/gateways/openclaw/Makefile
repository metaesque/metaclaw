SERVICE_TITLE = OpenClaw Gateway Service
SERVICE_NAME = openclaw-gateway

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include $(FRAMEWORK_ROOT)/services/proxy/.env
-include .env
export

LOG_READY_SIGNAL = listening on

.PHONY: check-status check-logs gui gui-setup gui-status tui patch clean-local-state onboard prep-instructions sync symlink

pre-up:
	@echo "[$(SERVICE_TITLE)] Ensuring static Docker CLI is available for DooD (Docker-out-of-Docker)..."
	@mkdir -p bin
	@if [ -d ./bin/docker ]; then \
		echo "Removing invalid docker directory..."; \
		rm -rf ./bin/docker; \
	fi
	@if [ ! -f ./bin/docker ]; then \
		ARCH=$$(uname -m); \
		if [ "$$ARCH" = "x86_64" ]; then DOCKER_ARCH="x86_64"; \
		elif [ "$$ARCH" = "aarch64" ] || [ "$$ARCH" = "arm64" ]; then DOCKER_ARCH="aarch64"; \
		else echo "Unsupported architecture: $$ARCH"; exit 1; fi; \
		echo "Downloading static Docker CLI for $$DOCKER_ARCH..."; \
		curl -sSL "https://download.docker.com/linux/static/stable/$$DOCKER_ARCH/docker-24.0.9.tgz" | tar xz -C bin --strip-components=1 docker/docker; \
		chmod +x ./bin/docker; \
	fi

post-up:
	@date +%Y%m%d-%H%M%S > .start

post-check-status:
	@echo "Bypassing GUI healthcheck until native configuration is established."

clean-state:: clean-local-state

clean-local-state:
	@echo "[$(SERVICE_TITLE)] Wiping local application state..."
	@if [ -d config/agents/main/sessions ] && [ -f .start ]; then \
		START_TIME=$$(cat .start); \
		DEST="$(EXTERNAL_DRIVE_PATH)/openclaw-prompts/$$START_TIME"; \
		echo "[$(SERVICE_TITLE)] Archiving OpenClaw sessions to $$DEST..."; \
		mkdir -p "$$DEST"; \
		cp -R config/agents/main/sessions/* "$$DEST/" 2>/dev/null || true; \
	fi
	@rm -rf config .openclaw_state bin/docker .start
	@rm -f seed-config.json index.html index.md
	@rm -f $(FRAMEWORK_ROOT)/config
	@echo "[$(SERVICE_TITLE)] Purging dynamically generated sandbox artifacts..."
	@docker ps -a -q --filter "ancestor=openclaw-sandbox:bookworm-slim" | xargs -r docker rm -f || true
	@docker ps -a -q --filter "name=openclaw-sandbox" | xargs -r docker rm -f || true
	@docker rmi openclaw-sandbox:bookworm-slim 2>/dev/null || true

# Apply target fixed to trigger patching and non-destructive reload
apply: symlink
	@echo "[$(SERVICE_TITLE)] Reconciling gateway container..."
	@mkdir -p config
	@$(MAKE) --no-print-directory patch

# Creates a human-friendly symlink from project root to service config
symlink:
	@if [ ! -L "$(FRAMEWORK_ROOT)/config" ]; then \
		echo "Creating root symlink to $(SERVICE_TITLE) config..."; \
		ln -s services/gateways/openclaw/config $(FRAMEWORK_ROOT)/config; \
	fi

patch:
	@echo "[$(SERVICE_TITLE)] Patching OpenClaw routing and configuration..."
	@$(PYTHON_BIN) patch_routing.py
	@cp openclaw.config.js config/openclaw.config.js
	@echo "[$(SERVICE_TITLE)] Restarting gateway to apply patches and load config..."
	@$(MAKE) --no-print-directory restart

sync:
	@echo "[$(SERVICE_TITLE)] Forcing native filesystem sync to invalidate cache..."
	@docker exec $(SERVICE_NAME) find /root/.openclaw/workspace -type f -exec touch {} +
	@echo "[$(SERVICE_TITLE)] Workspace cache hot-reloaded successfully."

prep-instructions:
	@echo "Hydrating Markdown instructions with Live API Key..."
	@$(PYTHON_BIN) -c "import os; key=open('$(FRAMEWORK_ROOT)/services/proxy/.env').read().split('ACTIVE_PROXY_KEY=')[1].split('\n')[0].strip() if os.path.exists('$(FRAMEWORK_ROOT)/services/proxy/.env') else 'ERROR_KEY_NOT_FOUND'; open('index.md', 'w').write(open('index.template.md').read().replace('__MASTER_KEY__', key))"
	@$(MAKE) --no-print-directory docs

onboard:
	@echo "[$(SERVICE_TITLE)] Attaching to interactive wizard..."
	@docker exec -it $(SERVICE_NAME) openclaw agents add main

# ==============================================================================
# USER INTERFACE TARGETS
# ==============================================================================
# MANDATE: Do NOT use bin/browser.py for these GUI targets.
# The Dashboard must ALWAYS open in the user's personal native browser via $(OPEN_CMD).
# ==============================================================================

gui:
	@echo "[$(SERVICE_TITLE)] Retrieving authentication token..."
	@URL=$$(docker exec $(SERVICE_NAME) openclaw dashboard | grep "Dashboard URL:" | awk '{print $$3}'); \
	if [ -z "$$URL" ]; then \
		echo "FATAL: Failed to retrieve Dashboard URL."; \
		exit 1; \
	fi; \
	echo "[$(SERVICE_TITLE)] Opening $$URL in default browser..."; \
	if [ -n "$(OPEN_CMD)" ] && command -v $(OPEN_CMD) >/dev/null 2>&1; then \
		$(OPEN_CMD) "$$URL"; \
	else \
		echo "Please manually navigate to: $$URL"; \
	fi

gui-setup:
	@echo "[$(SERVICE_TITLE)] Initiating one-time GUI infrastructure setup..."
	@$(MAKE) --no-print-directory wait-healthy
	@if ! curl -fsS http://127.0.0.1:$(OPENCLAW_PORT)/healthz > /dev/null 2>&1; then \
		echo "[$(SERVICE_TITLE)] Connection refused. Executing state reconciliation..."; \
		$(MAKE) --no-print-directory patch; \
		$(MAKE) --no-print-directory wait-healthy; \
	else \
		echo "[$(SERVICE_TITLE)] Network binding appears healthy. Proceeding to pairing..."; \
	fi
	@$(MAKE) --no-print-directory gui
	@echo "--------------------------------------------------------------------------------"
	@echo "ACTION REQUIRED: Please wait while the browser connects."
	@echo "The framework will monitor for the background pairing request and auto-approve it."
	@echo "Note: The 'pairing required' message in the UI is informational, not a button."
	@echo "--------------------------------------------------------------------------------"
	@for i in $$(seq 1 15); do \
		sleep 2; \
		REQ_ID=$$(docker exec $(SERVICE_NAME) openclaw devices list --json 2>/dev/null | jq -r '.pending[0].requestId // .pending[0].deviceId // empty'); \
		if [ -n "$$REQ_ID" ] && [ "$$REQ_ID" != "null" ]; then \
			echo "[$(SERVICE_TITLE)] Pairing request detected: $$REQ_ID"; \
			docker exec $(SERVICE_NAME) openclaw devices approve $$REQ_ID >/dev/null 2>&1; \
			echo "[$(SERVICE_TITLE)] Setup complete. UI should now be operational."; \
			$(MAKE) --no-print-directory gui; \
			exit 0; \
		fi; \
	done; \
	echo "TIMEOUT: No pairing request detected. If the UI is still locked, please re-run 'make gui-setup'."

gui-status:
	@echo "================================================================================"
	@echo "1. DASHBOARD STATUS"
	@echo "================================================================================"
	@docker exec $(SERVICE_NAME) openclaw dashboard || true
	@echo ""
	@echo "================================================================================"
	@echo "2. DEVICE LIST (TABULAR)"
	@echo "================================================================================"
	@docker exec -e COLUMNS=200 $(SERVICE_NAME) openclaw devices list || true
	@echo ""
	@echo "================================================================================"
	@echo "3. DEVICE LIST (JSON)"
	@echo "================================================================================"
	@docker exec $(SERVICE_NAME) openclaw devices list --json || true

tui:
	@echo "[$(SERVICE_TITLE)] Attaching to interactive terminal..."
	@docker exec -it $(SERVICE_NAME) openclaw tui

tst:
	@echo "- ./config:$(OPENCLAW_INTERNAL_HOME)/.openclaw"
	@echo "- $(OPENCLAW_WORKSPACE):$(OPENCLAW_INTERNAL_HOME)/.openclaw/workspace"
