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
	@if [ -f .metal ]; then \
		echo "Bare-metal Tailscale active. Skipping container diagnostics." > verification.log; \
	else \
		echo "--- 1. Daemon Status ---" > verification.log; \
		docker exec $(SERVICE_NAME) tailscale status >> verification.log || echo "DAEMON_UNREACHABLE" >> verification.log; \
		if grep -q "DAEMON_UNREACHABLE" verification.log; then echo "FATAL: Tailscale daemon is unreachable."; exit 1; fi; \
	fi

clean-state::
	@echo "[$(SERVICE_TITLE)] Cleaned state."
