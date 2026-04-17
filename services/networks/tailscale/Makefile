SERVICE_TITLE = Tailscale Network Service
SERVICE_NAME = tailscale
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

pre-up:
	@if [ "$$(uname -s)" = "Darwin" ]; then \
		echo "================================================================================"; \
		echo "WARNING: Docker 'host' networking is fundamentally unsupported on macOS."; \
		echo "Please install the native Tailscale app from the Mac App Store instead."; \
		echo "The Docker container will still boot to provide Funnel/Webhook ingress capabilities,"; \
		echo "but it will NOT expose the Mac host OS itself to the Tailnet."; \
		echo "================================================================================"; \
		sleep 3; \
	fi

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Tailscale Connection Status ---" > verification.log
	@docker exec $(SERVICE_NAME) tailscale status >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@cat verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Tailscale daemon is unreachable."; exit 1; fi
	@if grep -q "Logged out" verification.log; then echo "FATAL: Tailscale is not authenticated. Check TAILSCALE_AUTHKEY."; exit 1; fi
	@echo "SUCCESS: Tailscale is connected and authenticated."

clean-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Tailscale machine state..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/tailscale-state
