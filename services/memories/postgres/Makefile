SERVICE_TITLE = PostgreSQL Database Service
SERVICE_NAME = postgres-db
DOCKER_SHELL_CMD = psql -U $(POSTGRES_SUPER_USER) -d postgres

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = database system is ready to accept connections

.PHONY: update-env

update-env: .env

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. Roles Check ---" > verification.log
	@docker exec -e PAGER=cat $(SERVICE_NAME) psql -U $(POSTGRES_SUPER_USER) -d postgres -c "\du" >> verification.log
	@echo "\n--- 2. Database Existence Check ---" >> verification.log
	@docker exec -e PAGER=cat $(SERVICE_NAME) psql -U $(POSTGRES_SUPER_USER) -d postgres -c "\l" >> verification.log
	@echo "\n--- 3. Extension Check (openclaw_db) ---" >> verification.log
	@docker exec -e PAGER=cat $(SERVICE_NAME) psql -U $(POSTGRES_SUPER_USER) -d openclaw_db -c "\dx" >> verification.log
	@cat verification.log
	@if ! grep -q "litellm_app" verification.log; then echo "FATAL: Postgres Role check failed."; exit 1; fi
	@if ! grep -q "openclaw_db" verification.log; then echo "FATAL: Postgres Database existence check failed."; exit 1; fi
	@if ! grep -q "vector" verification.log; then echo "FATAL: Postgres Vector extension check failed."; exit 1; fi

clean-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Postgres data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/openclaw-postgres-data
