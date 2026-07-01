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
-include $(SERVICES_DIR)/vcses/.env
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
DOCKER_SUBDIRS = $(SERVICES_DIR)/gateway $(SERVICES_DIR)/proxy-reverse $(SERVICES_DIR)/browser $(SERVICES_DIR)/fetcher $(SERVICES_DIR)/searcher $(SERVICES_DIR)/ci $(SERVICES_DIR)/event $(SERVICES_DIR)/vcses $(SERVICES_DIR)/tracer $(SERVICES_DIR)/secret $(SERVICES_DIR)/queue $(SERVICES_DIR)/sandbox $(SERVICES_DIR)/iam $(SERVICES_DIR)/proxy $(SERVICES_DIR)/cache $(SERVICES_DIR)/memory $(SERVICES_DIR)/logger $(SERVICES_DIR)/network
BARE_SUBDIRS = $(SERVICES_DIR)/runner
GATEWAY_SUBDIR = $(SERVICES_DIR)/gateway

# Boot order explicitly defined to capture initial logs before upstream
# services start
WIZARD_BOOT_ORDER = $(SERVICES_DIR)/network $(SERVICES_DIR)/logger $(SERVICES_DIR)/memory $(SERVICES_DIR)/cache $(SERVICES_DIR)/secret $(SERVICES_DIR)/iam $(SERVICES_DIR)/sandbox $(SERVICES_DIR)/runner $(SERVICES_DIR)/queue $(SERVICES_DIR)/proxy $(SERVICES_DIR)/tracer $(SERVICES_DIR)/vcses $(SERVICES_DIR)/event $(SERVICES_DIR)/ci $(SERVICES_DIR)/searcher $(SERVICES_DIR)/fetcher $(SERVICES_DIR)/browser $(SERVICES_DIR)/proxy-reverse $(SERVICES_DIR)/gateway

# Meta-level reasoning. Must be a directory relative to the directory this
# Makefile resides in!
METACLAW_METAPATH=workspace/src/metaclaw

.PHONY: setup bootstrap clean-network network manifest newcode undock factory-reset factory-reset-soft factory-reset-hard wizard wizard-batch wizard-run apply status symlinks gui zip tmp/metaclaw.zip docs sync-cluster todo clean-state meta-push meta-cmp meta-pull meta-down install-docker

# ==============================================================================
# ENVIRONMENT BOOTSTRAPPING
# ==============================================================================

# WHAT IT DOES: Analyzes the host OS and automatically installs Docker Engine or OrbStack.
# WHY IT EXISTS: Streamlines bare-metal node provisioning before 'make setup'.
install-docker:
	@echo "################################################################################"
	@echo "# INSTALLING DOCKER ENGINE"
	@echo "################################################################################"
	@bash ./bin/install_docker.sh

# WHAT IT DOES: Ensures the Python virtual environment exists and dependencies are installed.
# WHY IT EXISTS: Prevents global pip pollution and ensures deterministic execution of framework scripts.
$(PYTHON_BIN):
	@$(MAKE) --no-print-directory -C bin install-code

# WHAT IT DOES: Instantiates `.env` files across the framework from `.env.template` files.
# WHY IT EXISTS: Required for injecting host-specific configurations (ports, keys) safely into containers.
.env: .env.template $(wildcard .env.json) | $(PYTHON_BIN)
	$(PYTHON_BIN) ./bin/env_instantiate.py $(if $(filter factory-reset% clean% undock,$(MAKECMDGOALS)),--teardown)

# WHAT IT DOES: Analyzes the hardware footprint, assigns a Tier (0-5), and generates `profile.json`.
# WHY IT EXISTS: This is the core cluster-state generator required before deploying services.
setup: | $(PYTHON_BIN)
	@echo "################################################################################"
	@echo "# INITIATING METACLAW ENVIRONMENT SETUP"
	@echo "################################################################################"
	@echo "\n[Setup] Step 1: Profiling local hardware and establishing cluster tier..."
	@$(PYTHON_BIN) ./bin/sysprofile.py
	@echo "\n[Setup] Step 2: Orchestrating dynamic symlinks and cross-node routing..."
	@$(MAKE) --no-print-directory symlinks
	@echo "\n[Setup] Step 3: User Customization (Modules & Workspace)..."
	@$(PYTHON_BIN) ./bin/customize.py
	@echo "\n[Setup] Step 4: Compiling modular taxonomy into documentation..."
	@$(PYTHON_BIN) ./bin/compile_md.py --setup
	@echo "\n[Setup] Step 5: Instantiating global environment variables..."
	@$(MAKE) --no-print-directory .env
	@echo "################################################################################"
	@echo "# SETUP COMPLETE. Proceed by running: make wizard"
	@echo "################################################################################"

# ==============================================================================
# ORCHESTRATION & NETWORKING
# ==============================================================================

# WHAT IT DOES: Reads `profile.json` and creates filesystem symlinks mapping generic services to specific providers.
# WHY IT EXISTS: Allows dynamic swapping of components (e.g., swapping `searxng` for `tavily`) without rewriting Makefiles.
symlinks: | $(PYTHON_BIN)
	@echo "Executing Python Cluster Orchestrator..."
	@$(PYTHON_BIN) ./bin/orchestrate.py

# WHAT IT DOES: Pushes the local `profile.json` state to remote nodes defined in the cluster array.
# WHY IT EXISTS: Enables multi-node orchestration, allowing the Gateway on Node A to route traffic to the Runner on Node B.
sync-cluster: | $(PYTHON_BIN)
	@echo "Synchronizing profile.json across cluster nodes..."
	@$(PYTHON_BIN) ./bin/sync_cluster.py

# WHAT IT DOES: Initializes symlinks and establishes the internal Docker bridge network.
bootstrap: symlinks network
	@echo "Global infrastructure bootstrap complete."

# WHAT IT DOES: Creates the isolated `openclaw-network` for internal container communication.
network:
	@if ! docker network ls | grep -q "$(NETWORK_NAME)"; then \
		echo "Creating shared Docker network: $(NETWORK_NAME)..."; \
		docker network create $(NETWORK_NAME); \
	else \
		echo "Network $(NETWORK_NAME) already exists. Skipping."; \
	fi

# WHAT IT DOES: Destroys the shared Docker network.
clean-network:
	@echo "Attempting to remove $(NETWORK_NAME)..."
	@if docker network ls | grep -q "$(NETWORK_NAME)"; then \
		docker network rm $(NETWORK_NAME) || echo "Failed to remove network. Ensure no containers are attached."; \
	else \
		echo "Network $(NETWORK_NAME) already removed."; \
	fi

# ==============================================================================
# LIFECYCLE MANAGEMENT (START / STOP / STATUS)
# ==============================================================================

# WHAT IT DOES: Gracefully shuts down all Docker containers defined in the framework in reverse-dependency order.
# WHY IT EXISTS: Prevents orphan containers or locked resources during a system halt.
undock:
	@for dir in $(DOCKER_SUBDIRS); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then echo "WARNING: [$$REAL_DIR] Provider unimplemented (No Makefile). Skipping 'down'."; continue; fi; \
		echo "################################################################################"; \
		echo "# Executing teardown in $$REAL_DIR..."; \
		echo "################################################################################"; \
		OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR down || true; \
	done

# WHAT IT DOES: Compares running container configurations against physical `.env` files and restarts/rebuilds them if mismatched.
# WHY IT EXISTS: The standard deployment command for pushing infrastructure changes gracefully.
apply: symlinks
	@echo "################################################################################"
	@echo "# RECONCILING GLOBAL INFRASTRUCTURE STATE"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then echo "WARNING: [$$REAL_DIR] Provider unimplemented (No Makefile). Skipping 'apply'."; continue; fi; \
		echo "[Root] Evaluating state in $$REAL_DIR..."; \
		$(MAKE) --no-print-directory -C $$REAL_DIR apply || true; \
	done

# WHAT IT DOES: Executes `docker ps` for all managed containers, filtered to exclude unmanaged host containers.
status:
	@echo "################################################################################"
	@echo "# GLOBAL INFRASTRUCTURE STATUS"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then continue; fi; \
		echo "--------------------------------------------------------------------------------"; \
		echo "[Root] Checking status of $$REAL_DIR..."; \
		$(MAKE) --no-print-directory -C $$REAL_DIR status || true; \
	done

# WHAT IT DOES: Injects the secure access token and opens the OpenClaw Dashboard in the native host OS browser.
gui:
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) gui

# WHAT IT DOES: opens the OpenClaw TUI
tui:
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) tui

# ==============================================================================
# WIZARD BOOT SEQUENCE
# ==============================================================================

# WHAT IT DOES: Interactive deployment sequence. Prompts user to confirm configurations and verify diagnostic logs sequentially.
wizard: INTERACTIVE=1
wizard: wizard-run

# WHAT IT DOES: Unattended deployment sequence. Bypasses all human-in-the-loop prompts. Assumes `.env.json` secrets are intact.
wizard-batch: INTERACTIVE=0
wizard-batch: wizard-run

# WHAT IT DOES: Auto-generates local HTML documentation from Markdown files.
docs: | $(PYTHON_BIN)
	@echo "Compiling root documentation..."
	@$(PYTHON_BIN) ./bin/compile_md.py -i docs/index.md --html

# The core execution loop for booting the cluster in a safe, dependency-aware sequence.
wizard-run: bootstrap docs
	@echo "################################################################################"
	@echo "# INITIATING FRAMEWORK SETUP"
	@echo "################################################################################"
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/docs/index.html"; \
	fi
	@if [ "$(INTERACTIVE)" = "1" ] || [ ! -f .env.json ] || grep -q "change_me" .env.json 2>/dev/null; then \
		echo "ATTENTION: The setup wizard will now request several API keys."; \
		echo "If you require remote WAN access, please generate a Tailscale Auth Key at:"; \
		echo "https://login.tailscale.com/admin/settings/keys"; \
		echo "Press ENTER to continue when you are ready..."; \
		read dummy < /dev/tty; \
	fi
	@mkdir -p .logs
	@echo "################################################################################"
	@echo "# PRE-FLIGHT ENVIRONMENT CONFIGURATION"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then continue; fi; \
		if [ -f "$$REAL_DIR/.metal" ] || [ -f "$$REAL_DIR/docker-compose.yml" ]; then \
			if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$REAL_DIR/index.md" ]; then \
				$(PYTHON_BIN) $(CURDIR)/bin/compile_md.py -i $$REAL_DIR/index.md --html; \
				$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$$REAL_DIR/index.html#env.vars"; \
			fi; \
			cd $$REAL_DIR && $(PYTHON_BIN) $(CURDIR)/bin/env_instantiate.py -v; \
			if grep -q "prep-instructions:" Makefile; then \
				$(MAKE) --no-print-directory prep-instructions; \
			fi; \
			cd $(CURDIR); \
			if [ "$(INTERACTIVE)" = "1" ]; then \
				comp=$$(basename $$REAL_DIR); \
				printf "$$comp environment is set. Proceed? [Y/n] "; \
				read answer < /dev/tty; \
				if [ "$$answer" != "" ] && [ "$$answer" != "Y" ] && [ "$$answer" != "y" ] && [ "$$answer" != "yes" ]; then \
					echo "Setup aborted by user."; exit 1; \
				fi; \
				echo "======================================================================"; \
			fi; \
		fi; \
	done
	@echo "################################################################################"
	@echo "# DEPLOYING CLUSTER INFRASTRUCTURE"
	@echo "################################################################################"
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then echo "WARNING: [$$REAL_DIR] Provider unimplemented (No Makefile). Skipping deploy."; continue; fi; \
		echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"; \
		echo "[Root] Deploying $$REAL_DIR..."; \
		if [ -f "$$REAL_DIR/.metal" ] || [ -f "$$REAL_DIR/docker-compose.yml" ]; then \
			if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$REAL_DIR/index.html" ]; then \
				$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$$REAL_DIR/index.html#diagnostic-checks"; \
			fi; \
			$(MAKE) --no-print-directory -C $$REAL_DIR apply || true; \
			$(MAKE) --no-print-directory -C $$REAL_DIR wait-healthy || true; \
			$(MAKE) --no-print-directory -C $$REAL_DIR check-status || true; \
			if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$REAL_DIR/index.html" ]; then \
				printf "Verify diagnostics for $$REAL_DIR. Proceed? [Y/n] "; \
				read answer < /dev/tty; \
				if [ "$$answer" != "" ] && [ "$$answer" != "Y" ] && [ "$$answer" != "y" ] && [ "$$answer" != "yes" ]; then \
					echo "Setup aborted by user."; exit 1; \
				fi; \
			fi; \
		else \
			$(MAKE) --no-print-directory -C $$REAL_DIR apply || true; \
		fi; \
	done
	@echo "################################################################################"
	@echo "# APPLYING GATEWAY CONFIGURATION"
	@echo "################################################################################"
	@echo "Applying routing patch..."
	@$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) patch
	@echo "################################################################################"
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		echo "# WIZARD COMPLETE. LAUNCHING WEB GUI..."; \
		echo "################################################################################"; \
		echo ""; \
		echo "Waiting for OpenClaw Gateway to finish booting..."; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) wait-healthy; \
		$(PYTHON_BIN) ./bin/browser.py --close; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) gui-setup; \
	else \
		echo "# BATCH WIZARD COMPLETE. ALL SYSTEMS ONLINE."; \
		echo "################################################################################"; \
	fi

# ==============================================================================
# SYSTEM PURGE & RESET TARGETS
# ==============================================================================

# WHAT IT DOES: Deletes ephemeral files (`verification.log`, cached `.html` pages, `.state_*` flags) globally.
# WHY IT EXISTS: Cleans up the developer workspace without harming secrets or databases.
clean-state:
	@echo "################################################################################"
	@echo "# CLEANING LOCAL STATE ACROSS ALL SERVICES"
	@echo "################################################################################"
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then continue; fi; \
		OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR clean-state || echo "Warning: $$REAL_DIR clean-state failed."; \
	done

# WHAT IT DOES: Triggers `factory-reset-soft` as the default reset behavior.
factory-reset: factory-reset-soft

# WHAT IT DOES: Tears down all containers, destroys the network, and wipes `.env` text files.
# WHY THIS DEFAULT: **CRITICAL** - It explicitly PRESERVES `.env.json` (your cached secrets), `profile.json`, and all persistent external data.
#   This is the safest way to bounce a broken framework.
factory-reset-soft: undock clean-network
	@echo "################################################################################"
	@echo "# INITIATING FACTORY RESET (SOFT - PRESERVING SECRETS & DATA)"
	@echo "################################################################################"
	@$(MAKE) --no-print-directory clean-state
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		rm -f "$$REAL_DIR/.env"; \
	done
	@echo "Purging global runtime state..."
	@rm -f .env tmp/metaclaw.txt docs/index.html .env.cluster
	@rm -rf .logs
	@$(PYTHON_BIN) ./bin/browser.py --close >/dev/null 2>&1 || true
	@find . -name "*.env.tmp" -type f -delete 2>/dev/null || true
	@echo "Soft reset complete. External data, .env.json files, profile.json, and python .venv preserved."

# WHAT IT DOES: The Nuclear Option. Destroys everything, including cached `.env.json` secrets and the hardware `profile.json`.
# WHY IT EXISTS: Required if the user wishes to redeploy from scratch with entirely new API keys or a different hardware cluster configuration.
factory-reset-hard: factory-reset-soft
	@echo "################################################################################"
	@echo "# PURGING ALL SECRETS AND PERSISTENT DATA (HARD RESET)"
	@echo "################################################################################"
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		if [ ! -f "$$REAL_DIR/Makefile" ]; then rm -f "$$REAL_DIR/.env.json"; continue; fi; \
		OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR clobber-data || echo "Warning: $$REAL_DIR clobber-data failed."; \
		rm -f "$$REAL_DIR/.env.json"; \
	done
	@rm -f .env.json profile.json
	@rm -rf bin/.venv
	@echo "Hard reset complete. All secrets, data, and environments destroyed."

# ==============================================================================
# PACKAGING & ANALYSIS TOOLS
# ==============================================================================

# WHAT IT DOES: Creates a deployable ZIP archive of the framework respecting `MANIFEST.files`.
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

# WHAT IT DOES: Concatenates the entire framework into a single `.txt` payload for injection into an LLM context window.
txt: tmp/metaclaw.txt
tmp/metaclaw.txt: FORCE | $(PYTHON_BIN)
	@mkdir -p tmp
	$(PYTHON_BIN) ./bin/newcode.py -s docs/MANIFEST.files > tmp/metaclaw.txt
	@echo "Manifest generated at: tmp/metaclaw.txt"

# WHAT IT DOES: Parses a block of AI-generated Markdown and writes the files back to disk atomically.
newcode: | $(PYTHON_BIN)
	@echo "Applying AI-generated changes from ./input..."
	$(PYTHON_BIN) ./bin/newcode.py ./input

# WHAT IT DOES: Analyzes PostgreSQL logs to calculate actual API spend over the last N hours.
spend-%: | $(PYTHON_BIN)
	$(PYTHON_BIN) bin/postgres_analysis.py --spend --hours="$*"
jspend-%: | $(PYTHON_BIN)
	$(PYTHON_BIN) bin/postgres_analysis.py --spend --hours="$*" -j

# WHAT IT DOES: Scans the codebase for TODO tags and generates a consolidated report.
todo: | $(PYTHON_BIN)
	@$(PYTHON_BIN) ./bin/todo.py

# ==============================================================================
# AGENT DEVELOPMENT ENVIRONMENT (GITOPS)
# ==============================================================================

# WHAT IT DOES: Provisions a Git clone of MetaClaw into the agent's workspace.
# WHY IT EXISTS: Allows the agent to autonomously develop the framework via standard Git PRs.
meta-push:
	@echo "################################################################################"
	@echo "# [GitOps] Provisioning MetaClaw repository in agent workspace..."
	@echo "################################################################################"
	@if [ ! -d $(METACLAW_METAPATH) ]; then \
		git clone https://github.com/metaesque/metaclaw.git $(METACLAW_METAPATH); \
	else \
		cd $(METACLAW_METAPATH) && git pull; \
	fi
	@echo "Agent workspace ready at $(METACLAW_METAPATH)"

# WHAT IT DOES: Reminds the user of the new GitOps workflow.
# WHY IT EXISTS: Replaces the old local diffing tool now that MetaClaw is public.
meta-cmp:
	@echo "################################################################################"
	@echo "# [GitOps] Local diffing is deprecated."
	@echo "# The agent should now commit and push its changes to a feature branch."
	@echo "# Please review the Pull Request directly on GitHub:"
	@echo "# https://github.com/metaesque/metaclaw/pulls"
	@echo "################################################################################"

# WHAT IT DOES: Pulls the merged changes from GitHub into the live host.
# WHY IT EXISTS: Closes the loop on agent-driven development securely.
meta-pull:
	@echo "################################################################################"
	@echo "# [GitOps] Pulling merged updates from the public repository to the live host..."
	@echo "################################################################################"
	@git pull origin main
	@echo "Run 'make apply' to deploy the new state."

# WHAT IT DOES: Cleans up and deletes the staging environment clone.
meta-down:
	@if [ -d $(METACLAW_METAPATH) ] ; then \
		echo ""; \
		printf "Destroy $(METACLAW_METAPATH)? [y/N] "; \
		read answer < /dev/tty; \
		if [ "$$answer" == "Y" ] || [ "$$answer" == "y" ]; then \
			rm -rf $(METACLAW_METAPATH); \
			echo "NOTE: Removed $(METACLAW_METAPATH)"; \
		else \
			echo "NOTE: Did NOT remove $(METACLAW_METAPATH)"; \
		fi; \
	fi

FORCE:

tst:
	echo "PYTHON_BIN=$(PYTHON_BIN)"
