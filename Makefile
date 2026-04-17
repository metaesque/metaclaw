# Include global infrastructure state first
SERVICES_DIR ?= services

-include .env
-include .env.cluster
-include $(SERVICES_DIR)/network/.env
-include $(SERVICES_DIR)/logger/.env
-include $(SERVICES_DIR)/proxy/.env
-include $(SERVICES_DIR)/gateway/.env
-include $(SERVICES_DIR)/cache/.env
-include $(SERVICES_DIR)/memory/.env
-include $(SERVICES_DIR)/runner/.env
-include $(SERVICES_DIR)/sandbox/.env
-include $(SERVICES_DIR)/browser/.env
-include $(SERVICES_DIR)/fetcher/.env
-include $(SERVICES_DIR)/searcher/.env
-include $(SERVICES_DIR)/ci/.env
-include $(SERVICES_DIR)/event/.env
-include $(SERVICES_DIR)/vcs/.env
-include $(SERVICES_DIR)/secret/.env
-include $(SERVICES_DIR)/tracer/.env
-include $(SERVICES_DIR)/iam/.env
-include $(SERVICES_DIR)/proxy-reverse/.env
-include $(SERVICES_DIR)/queue/.env
export

# OS-Agnostic Open Command
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	OPEN_CMD := open
else
	OPEN_CMD := xdg-open
endif
export OPEN_CMD

# Centralized, isolated Python environment
PYTHON_BIN ?= $(CURDIR)/bin/.venv/bin/python

# Teardown order (Reverse dependencies)
DOCKER_SUBDIRS = $(SERVICES_DIR)/network $(SERVICES_DIR)/logger $(SERVICES_DIR)/gateway $(SERVICES_DIR)/proxy-reverse $(SERVICES_DIR)/iam $(SERVICES_DIR)/proxy $(SERVICES_DIR)/cache $(SERVICES_DIR)/memory $(SERVICES_DIR)/sandbox $(SERVICES_DIR)/queue $(SERVICES_DIR)/browser $(SERVICES_DIR)/fetcher $(SERVICES_DIR)/searcher $(SERVICES_DIR)/ci $(SERVICES_DIR)/event $(SERVICES_DIR)/vcs $(SERVICES_DIR)/secret $(SERVICES_DIR)/tracer
BARE_SUBDIRS = $(SERVICES_DIR)/runner
GATEWAY_SUBDIR = $(SERVICES_DIR)/gateway

# Boot order explicitly defined to capture initial logs before upstream services start
WIZARD_BOOT_ORDER = $(SERVICES_DIR)/network $(SERVICES_DIR)/logger $(SERVICES_DIR)/memory $(SERVICES_DIR)/cache $(SERVICES_DIR)/secret $(SERVICES_DIR)/iam $(SERVICES_DIR)/sandbox $(SERVICES_DIR)/runner $(SERVICES_DIR)/queue $(SERVICES_DIR)/proxy $(SERVICES_DIR)/tracer $(SERVICES_DIR)/vcs $(SERVICES_DIR)/event $(SERVICES_DIR)/ci $(SERVICES_DIR)/searcher $(SERVICES_DIR)/fetcher $(SERVICES_DIR)/browser $(SERVICES_DIR)/proxy-reverse $(SERVICES_DIR)/gateway

.PHONY: setup bootstrap clean-network network manifest newcode undock factory-reset factory-reset-soft factory-reset-hard wizard wizard-batch wizard-run onboard-interactive onboard-batch apply onboard status symlinks gui zip tmp/metaclaw.zip docs sync-cluster todo

# Ensure the virtual environment exists before running Python scripts
$(PYTHON_BIN):
	@$(MAKE) --no-print-directory -C bin install-code

# Order-only prerequisite
.env: .env.template $(wildcard .env.json) | $(PYTHON_BIN)
	$(PYTHON_BIN) ./bin/env_instantiate.py $(if $(filter factory-reset% clean% undock,$(MAKECMDGOALS)),--teardown)

# Auto-generate dynamic symlinks for the service abstractions
symlinks: | $(PYTHON_BIN)
	@echo "Executing Python Cluster Orchestrator..."
	@$(PYTHON_BIN) ./bin/orchestrate.py

sync-cluster: | $(PYTHON_BIN)
	@echo "Synchronizing profile.json across cluster nodes..."
	@$(PYTHON_BIN) ./bin/sync_cluster.py

setup: | $(PYTHON_BIN)
	@echo "################################################################################"
	@echo "# INITIATING METACLAW ENVIRONMENT SETUP"
	@echo "################################################################################"
	@echo "\n[Setup] Step 1: Profiling local hardware and establishing cluster phase..."
	@$(PYTHON_BIN) ./bin/sysprofile.py
	@echo "\n[Setup] Step 2: Orchestrating dynamic symlinks and cross-node routing..."
	@$(MAKE) --no-print-directory symlinks
	@echo "\n[Setup] Step 3: Compiling modular taxonomy into documentation..."
	@$(PYTHON_BIN) ./bin/compile_md.py --setup
	@$(MAKE) --no-print-directory docs
	@echo "\n[Setup] Step 4: Instantiating global environment variables..."
	@$(MAKE) --no-print-directory .env
	@echo "################################################################################"
	@echo "# SETUP COMPLETE."
	@echo "# Proceed by running: make wizard"
	@echo "################################################################################"

bootstrap: symlinks network
	@echo "Global infrastructure bootstrap complete."

network:
	@if ! docker network ls | grep -q "$(NETWORK_NAME)"; then \
		echo "Creating shared Docker network: $(NETWORK_NAME)..."; \
		docker network create $(NETWORK_NAME); \
	else \
		echo "Network $(NETWORK_NAME) already exists. Skipping."; \
	fi

clean-network:
	@echo "Attempting to remove $(NETWORK_NAME)..."
	@if docker network ls | grep -q "$(NETWORK_NAME)"; then \
		docker network rm $(NETWORK_NAME) || echo "Failed to remove network. Ensure no containers are attached."; \
	else \
		echo "Network $(NETWORK_NAME) already removed."; \
	fi

undock:
	@for dir in $(DOCKER_SUBDIRS); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			echo "################################################################################"; \
			echo "# Executing teardown in $$dir..."; \
			echo "################################################################################"; \
			OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$dir down; \
		fi; \
	done

factory-reset: factory-reset-soft

factory-reset-soft: undock clean-network
	@echo "################################################################################"
	@echo "# INITIATING FACTORY RESET (SOFT - PRESERVING SECRETS & DATA)"
	@echo "################################################################################"
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$dir clean-state || echo "Warning: $$dir clean-state failed."; \
			rm -f "$$dir/.env"; \
		fi; \
	done
	@echo "Purging global runtime state..."
	@rm -f .env tmp/metaclaw.txt docs/index.html .env.cluster
	@rm -rf .logs
	@$(PYTHON_BIN) ./bin/browser.py --close >/dev/null 2>&1 || true
	@find . -name "*.env.tmp" -type f -delete 2>/dev/null || true
	@echo "Soft reset complete. External data, .env.json files, profile.json, and python .venv preserved."

factory-reset-hard: factory-reset-soft
	@echo "################################################################################"
	@echo "# PURGING ALL SECRETS AND PERSISTENT DATA (HARD RESET)"
	@echo "################################################################################"
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$dir clean-data || echo "Warning: $$dir clean-data failed."; \
			rm -f "$$dir/.env.json"; \
		fi; \
	done
	@rm -f .env.json profile.json
	@rm -rf bin/.venv
	@echo "Hard reset complete. All secrets, data, and environments destroyed."

wizard: INTERACTIVE=1
wizard: wizard-run

wizard-batch: INTERACTIVE=0
wizard-batch: wizard-run

docs: | $(PYTHON_BIN)
	@echo "Compiling root documentation..."
	@$(PYTHON_BIN) ./bin/compile_md.py -i docs/index.md --html

wizard-run: bootstrap docs
	@echo "################################################################################"
	@echo "# INITIATING FRAMEWORK SETUP"
	@echo "################################################################################"
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/docs/index.html"; \
	fi
	@echo "ATTENTION: The setup wizard will now request several API keys."
	@echo "If you require remote WAN access, please generate a Tailscale Auth Key at:"
	@echo "https://login.tailscale.com/admin/settings/keys"
	@echo "Press ENTER to continue when you are ready..."
	@read dummy < /dev/tty
	@mkdir -p .logs
	@echo "################################################################################"
	@echo "# PRE-FLIGHT ENVIRONMENT CONFIGURATION"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			if [ -f "$$dir/.metal" ] || [ -f "$$dir/docker-compose.yml" ]; then \
				if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$dir/index.md" ]; then \
					$(PYTHON_BIN) $(CURDIR)/bin/compile_md.py -i $$dir/index.md --html; \
					$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$$dir/index.html#env.vars"; \
				fi; \
				cd $$dir && $(PYTHON_BIN) $(CURDIR)/bin/env_instantiate.py -v; \
				cd $(CURDIR); \
				if [ "$(INTERACTIVE)" = "1" ]; then \
					comp=$$(basename $$dir); \
					printf "$$comp environment is set. Proceed? [Y/n] "; \
					read answer < /dev/tty; \
					if [ "$$answer" != "" ] && [ "$$answer" != "Y" ] && [ "$$answer" != "y" ] && [ "$$answer" != "yes" ]; then \
						echo "Setup aborted by user."; exit 1; \
					fi; \
					echo "======================================================================"; \
				fi; \
			fi; \
		fi; \
	done
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			if [ -f "$$dir/.metal" ] || [ -f "$$dir/docker-compose.yml" ]; then \
				echo "################################################################################"; \
				echo "# Booting $$dir..."; \
				echo "################################################################################"; \
				if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$dir/index.md" ]; then \
					$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$$dir/index.html"; \
				fi; \
				{ \
					$(MAKE) --no-print-directory -C $$dir up; \
					if grep -q "wait-healthy:" "$$dir/Makefile" || grep -q "wait-healthy:" ".Makefile.inherit"; then \
						$(MAKE) --no-print-directory -C $$dir wait-healthy; \
					fi; \
					$(MAKE) --no-print-directory -C $$dir check-logs 2>/dev/null || true; \
					$(MAKE) --no-print-directory -C $$dir check-status 2>/dev/null || true; \
				} 2>&1 | tee .logs/$$(basename $$dir).txt; \
				if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$dir/index.md" ]; then \
					echo ""; \
					printf "Does the INTEGRITY VERIFICATION output match HTML expectations? [Y/n] "; \
					read answer < /dev/tty; \
					if [ "$$answer" != "" ] && [ "$$answer" != "Y" ] && [ "$$answer" != "y" ]; then \
						echo "Wizard aborted by user."; exit 1; \
					fi; \
				fi; \
				echo ""; \
			fi; \
		fi; \
	done
	@echo "################################################################################"
	@echo "# GATEWAY CONFIGURATION REQUIRED"
	@echo "################################################################################"
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		$(MAKE) --no-print-directory onboard-interactive; \
	else \
		$(MAKE) --no-print-directory onboard-batch; \
	fi
	@echo "Applying routing patch..."
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) patch
	@echo "################################################################################"
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		echo "# WIZARD COMPLETE. LAUNCHING TERMINAL UI..."; \
		echo "################################################################################"; \
		echo "First Steps:"; \
		echo " - Type '/help' to see available commands."; \
		echo " - Type '/exit' or use Ctrl+C twice to leave the chat."; \
		echo ""; \
		echo "Waiting for OpenClaw Gateway to finish booting..."; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) wait-healthy; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) tui; \
		echo "Terminal UI exited. Launching Web GUI setup..."; \
		$(PYTHON_BIN) ./bin/browser.py --close; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) gui-setup; \
	else \
		echo "# BATCH WIZARD COMPLETE. ALL SYSTEMS ONLINE."; \
		echo "################################################################################"; \
	fi

onboard:
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) onboard

onboard-interactive:
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) prep-instructions
	@$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$(GATEWAY_SUBDIR)/index.html"
	@echo "Launching interactive onboarding TUI natively..."
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) onboard

onboard-batch:
	@echo "Executing automated batch onboarding via pexpect..."
	@$(PYTHON_BIN) ./$(GATEWAY_SUBDIR)/onboard_expect.py

apply: symlinks
	@echo "################################################################################"
	@echo "# RECONCILING GLOBAL INFRASTRUCTURE STATE"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			echo "[Root] Evaluating state in $$dir..."; \
			$(MAKE) --no-print-directory -C $$dir apply || true; \
		fi; \
	done

status:
	@echo "################################################################################"
	@echo "# GLOBAL INFRASTRUCTURE STATUS"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ] || [ -d "$$dir" ]; then \
			echo "--------------------------------------------------------------------------------"; \
			echo "[Root] Checking status of $$dir..."; \
			$(MAKE) --no-print-directory -C $$dir status || true; \
		fi; \
	done

gui:
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) gui

zip: tmp/metaclaw.zip

tmp/metaclaw.zip: FORCE | $(PYTHON_BIN)
	@echo "################################################################################"
	@echo "# PACKAGING FRAMEWORK"
	@echo "################################################################################"
	@if [ ! -f docs/MANIFEST.files ]; then echo "FATAL: docs/MANIFEST.files is missing."; exit 1; fi
	@rm -rf .tmp_pack tmp/metaclaw.zip
	@mkdir -p .tmp_pack tmp
	@while IFS= read -r file || [ -n "$$file" ]; do \
		if [ -f "$$file" ]; then \
			mkdir -p ".tmp_pack/$$(dirname "$$file")"; \
			cp "$$file" ".tmp_pack/$$file"; \
		else \
			echo "Warning: Tracked file $$file is missing from disk and will be omitted."; \
		fi; \
	done < docs/MANIFEST.files
	@cd .tmp_pack && zip -r -q ../tmp/metaclaw.zip .
	@rm -rf .tmp_pack
	@echo "Packaging complete: tmp/metaclaw.zip generated successfully."

txt: tmp/metaclaw.txt

tmp/metaclaw.txt: FORCE | $(PYTHON_BIN)
	@mkdir -p tmp
	$(PYTHON_BIN) ./bin/newcode.py -s docs/MANIFEST.files > tmp/metaclaw.txt
	@echo "Manifest generated at: tmp/metaclaw.txt"

newcode: | $(PYTHON_BIN)
	@echo "Applying AI-generated changes from ./input..."
	$(PYTHON_BIN) ./bin/newcode.py ./input

spend-%: | $(PYTHON_BIN)
	$(PYTHON_BIN) bin/postgres_analysis.py --spend --hours="$*"

jspend-%: | $(PYTHON_BIN)
	$(PYTHON_BIN) bin/postgres_analysis.py --spend --hours="$*" -j

todo: | $(PYTHON_BIN)
	@$(PYTHON_BIN) ./bin/todo.py

FORCE:
