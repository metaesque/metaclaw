SERVICE_TITLE = LiteLLM Proxy Service
SERVICE_NAME = litellm-proxy

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
# ARCHITECTURAL SHIFT: Consume the generic memory interface instead of hardcoded postgres
-include $(FRAMEWORK_ROOT)/services/memory/.env
-include .env
export

LOG_READY_SIGNAL = Uvicorn running on

.PHONY: newcode test

pre-up: router.json verify_service

RESTART_DEPS = config.yaml router.json advanced/patch_entrypoint.py advanced/entrypoint.sh

ROUTER_KIND ?= tiers

post-check-status:
	@echo "Running diagnostic suite (~30s) ..."
	@echo "--- 1. Web Server Health ---" > verification.log
	@curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $(ACTIVE_PROXY_KEY)" http://localhost:4000/v1/models >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "\n--- 2. Active Model Inventory ---" >> verification.log
	@curl -s http://localhost:4000/v1/models -H "Authorization: Bearer $(ACTIVE_PROXY_KEY)" | $(PYTHON_BIN) -c "import sys, json; data=json.load(sys.stdin); print(json.dumps([m['id'] for m in data['data']], indent=2))" >> verification.log
	@cat verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Web Server Health check failed."; exit 1; fi
	@if ! grep -q "simple-model" verification.log; then echo "FATAL: Model Inventory check failed."; exit 1; fi

router.json: utterances-$(ROUTER_KIND).yaml advanced/generate_router.py
	@echo "Compiling YAML into router.json..."
	@$(PYTHON_BIN) advanced/generate_router.py --kind $(ROUTER_KIND) --per_route 24

.state_recreate: | router.json

newcode:
	@$(PYTHON_BIN) advanced/newcode.py input

test:
	echo key is $(ACTIVE_PROXY_KEY)
