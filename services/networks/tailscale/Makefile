SERVICE_TITLE = Tailscale Network Service
SERVICE_NAME = tailscale
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

post-check-status:
	@echo "Running diagnostic suite..."
	@if [ -f "$(CURDIR)/.metal" ]; then \
		echo "--- 1. Bare-metal Daemon Status ---" > verification.log; \
		tailscale status >> verification.log || echo "DAEMON_UNREACHABLE" >> verification.log; \
		if grep -q "DAEMON_UNREACHABLE" verification.log; then echo "FATAL: Bare-metal Tailscale daemon is unreachable."; exit 1; fi; \
		echo "\nSUCCESS: Tailscale is connected and authenticated (Bare-Metal)." >> verification.log; \
	else \
		echo "--- 1. Docker Daemon Status ---" > verification.log; \
		docker exec $(SERVICE_NAME) tailscale status >> verification.log || echo "DAEMON_UNREACHABLE" >> verification.log; \
		if grep -q "DAEMON_UNREACHABLE" verification.log; then echo "FATAL: Docker Tailscale daemon is unreachable."; exit 1; fi; \
		echo "\nSUCCESS: Tailscale is connected and authenticated (Docker)." >> verification.log; \
	fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Tailscale is connected and authenticated (Bare-Metal)." "SUCCESS: Tailscale is connected and authenticated (Docker)."

clean-state::
	@echo "[$(SERVICE_TITLE)] Cleaned state."
