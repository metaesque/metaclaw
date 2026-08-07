SERVICE_TITLE = Neo4j Graph Database
SERVICE_NAME = neo4j-graphdb
DOCKER_SHELL_CMD = cypher-shell -u neo4j -p $(NEO4J_PASSWORD)

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = Started.

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. HTTP API Health ---" > verification.log
	@wget -qO- http://localhost:$(NEO4J_PORT_HTTP) > /dev/null && echo "HTTP_200_OK" >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: Neo4j API is unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "HTTP_200_OK"

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external Neo4j data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/neo4j-data
	@rm -rf $(EXTERNAL_DRIVE_PATH)/neo4j-logs
	@rm -rf $(EXTERNAL_DRIVE_PATH)/neo4j-import
	@rm -rf $(EXTERNAL_DRIVE_PATH)/neo4j-plugins
