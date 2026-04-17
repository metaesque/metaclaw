SERVICE_TITLE = Hardened Docker DooD Sandbox Service
SERVICE_NAME = docker-dood
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

post-check-status:
	@echo "SUCCESS: Sandbox is active, sterile, and network-isolated."
