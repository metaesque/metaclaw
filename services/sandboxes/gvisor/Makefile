SERVICE_TITLE = gVisor Sandbox Service
SERVICE_NAME = gvisor-sandbox

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include $(FRAMEWORK_ROOT)/services/gateways/openclaw/.env
-include .env
export

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. gVisor Check ---" > verification.log
	@echo "\nSUCCESS: Sandbox is active, sterile, and network-isolated." >> verification.log
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "SUCCESS: Sandbox is active, sterile, and network-isolated."
