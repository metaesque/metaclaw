SERVICE_TITLE = Redis Cache Service
SERVICE_NAME = redis-cache
DOCKER_SHELL_CMD = redis-cli

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Ready to accept connections tcp

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Connectivity Check ---" > verification.log
	@docker exec $(SERVICE_NAME) redis-cli ping >> verification.log
	@echo "\n--- 2. Memory Configuration ---" >> verification.log
	@docker exec $(SERVICE_NAME) redis-cli info memory | grep "maxmemory_human" >> verification.log
	@echo "\n--- 3. Eviction Policy ---" >> verification.log
	@docker exec $(SERVICE_NAME) redis-cli config get maxmemory-policy >> verification.log
	@cat verification.log
	@if ! grep -q "PONG" verification.log; then echo "FATAL: Redis connectivity failed."; exit 1; fi
	@if ! grep -q "512.00M" verification.log; then echo "FATAL: Redis memory limit not enforced."; exit 1; fi
	@if ! grep -q "allkeys-lru" verification.log; then echo "FATAL: Redis eviction policy incorrect."; exit 1; fi
