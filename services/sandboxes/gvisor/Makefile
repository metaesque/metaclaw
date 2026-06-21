SERVICE_TITLE = gVisor Sandbox Service
SERVICE_NAME = gvisor
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

.PHONY: up down status check-status wait-healthy clean-state clobber-data uninstall

up:
	@echo "[$(SERVICE_TITLE)] Checking for gVisor (runsc) installation..."
	@if ! command -v runsc >/dev/null 2>&1; then \
		echo "Installing gVisor..."; \
		ARCH=$$(uname -m); \
		if [ "$$ARCH" = "x86_64" ]; then ARCH="x86_64"; \
		elif [ "$$ARCH" = "aarch64" ] || [ "$$ARCH" = "arm64" ]; then ARCH="aarch64"; \
		else echo "Unsupported architecture: $$ARCH"; exit 1; fi; \
		URL="https://storage.googleapis.com/gvisor/releases/release/latest/$$ARCH"; \
		wget -q "$$URL/runsc" "$$URL/runsc.sha512" || { echo "Download failed"; exit 1; }; \
		sha512sum -c runsc.sha512 || { echo "Checksum failed"; exit 1; }; \
		rm -f *.sha512; \
		chmod a+rx runsc; \
		sudo mv runsc /usr/local/bin; \
		sudo /usr/local/bin/runsc install; \
		echo "Setting runsc as default Docker runtime..."; \
		sudo python3 -c 'import json, os; p="/etc/docker/daemon.json"; d=json.load(open(p)) if os.path.exists(p) and os.path.getsize(p)>0 else {}; d["default-runtime"]="runsc"; d.setdefault("runtimes", {})["runsc"]={"path": "/usr/local/bin/runsc"}; json.dump(d, open(p, "w"), indent=4)'; \
		sudo systemctl restart docker; \
		echo "gVisor installed successfully."; \
	else \
		echo "gVisor is already installed."; \
	fi

down:
	@echo "[$(SERVICE_TITLE)] gVisor is a host-level runtime. No active daemon containers to stop."

status:
	@if command -v runsc >/dev/null 2>&1; then \
		echo "gVisor is RUNNING (installed)."; \
	else \
		echo "gVisor is STOPPED (not installed)."; \
	fi

check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. runsc Binary Check ---" > verification.log
	@command -v runsc >> verification.log || echo "MISSING" >> verification.log
	@echo "\n--- 2. Docker Integration Check ---" >> verification.log
	@docker info | grep runsc >> verification.log || echo "NOT_REGISTERED" >> verification.log
	@echo "\nSUCCESS: gVisor runtime is available." >> verification.log
	@if grep -q "MISSING" verification.log; then echo "FATAL: runsc binary not found."; exit 1; fi
	@if grep -q "NOT_REGISTERED" verification.log; then echo "FATAL: runsc not registered with Docker."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: gVisor runtime is available."

wait-healthy: check-status

clean-state:
	@echo "[$(SERVICE_TITLE)] To fully uninstall gVisor, please run: make uninstall"

clobber-data:
	@echo "[$(SERVICE_TITLE)] No persistent data to purge for gVisor."

uninstall:
	@echo "[$(SERVICE_TITLE)] Uninstalling gVisor and reverting Docker configuration..."
	@if command -v runsc >/dev/null 2>&1; then \
		sudo rm -f /usr/local/bin/runsc; \
		echo "Removed runsc binary."; \
	else \
		echo "runsc binary not found."; \
	fi
	@echo "Updating /etc/docker/daemon.json to remove gVisor runtime hooks..."
	@sudo python3 -c 'import json, os; p="/etc/docker/daemon.json"; d=json.load(open(p)) if os.path.exists(p) and os.path.getsize(p)>0 else {}; d.pop("default-runtime", None); d.get("runtimes", {}).pop("runsc", None); json.dump(d, open(p, "w"), indent=4)'
	@echo "Restarting Docker daemon..."
	@sudo systemctl restart docker || echo "Failed to restart Docker. Please restart manually using: sudo systemctl restart docker"
	@echo "gVisor uninstall complete."
