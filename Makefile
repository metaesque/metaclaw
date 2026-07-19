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

.DEFAULT_GOAL := no_default

.PHONY: no_default
no_default:
	@echo "ERROR: Provide explicit target (e.g., make setup, make wizard-cluster, make apply)."
	@exit 1

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

.PHONY: setup setup-local bootstrap clean-network network manifest newcode __undock factory-reset factory-reset-soft factory-reset-hard wizard wizard-batch wizard-cluster wizard-run apply status status-local symlinks gui zip tmp/metaclaw.zip docs sync-cluster todo clean-state meta-push meta-cmp meta-pull meta-down install-docker mc-update customize wksp

define h1_title
	echo ""; \
	echo "############"; \
	echo "# $(1)"; \
	echo "--"
endef

define h2_title
	echo "============"; \
	echo "= $(1)"
endef

define h3_title
	echo "------------"; \
	echo "- $(1)"
endef

# ==============================================================================
# ENVIRONMENT BOOTSTRAPPING & UPDATES
# ==============================================================================

# WHAT IT DOES: Pulls the latest framework from GitHub and reconciles the containers.
# WHY IT EXISTS: The standard update loop for non-technical users.
mc-update:
	@$(call h1_title,"UPDATING METACLAW FRAMEWORK")
	@git pull origin main
	@$(MAKE) --no-print-directory apply

# WHAT IT DOES: Allows the user to modify their dynamic configuration (routing, paths).
# WHY IT EXISTS: Bypasses the full `setup` hardware profiler to quickly tweak settings.
customize: | $(PYTHON_BIN)
	@$(call h1_title,"MODIFYING METACLAW CONFIGURATION")
	@$(PYTHON_BIN) ./bin/customize.py
	@$(MAKE) --no-print-directory .env
	@echo "Run 'make apply' to enact any routing or path changes."

# WHAT IT DOES: Analyzes the host OS and automatically installs Docker Engine or OrbStack.
# WHY IT EXISTS: Streamlines bare-metal node provisioning before 'make setup'.
install-docker:
	@$(call h1_title,"INSTALLING DOCKER ENGINE")
	@bash ./bin/install_docker.sh

# WHAT IT DOES: Ensures the Python virtual environment exists and dependencies are installed.
# WHY IT EXISTS: Prevents global pip pollution and ensures deterministic execution of framework scripts.
$(PYTHON_BIN):
	@$(MAKE) --no-print-directory -C bin install-code

# WHAT IT DOES: Instantiates `.env` files across the framework from `.env.template` files.
# WHY IT EXISTS: Required for injecting host-specific configurations (ports, keys) safely into containers.
.env: .env.template $(wildcard .env.json) | $(PYTHON_BIN)
	$(PYTHON_BIN) ./bin/env_instantiate.py $(if $(filter factory-reset% clean% __undock,$(MAKECMDGOALS)),--teardown)

# WHAT IT DOES: The master cluster preparation target. Analyzes hardware, assigns providers,
#               pushes topology configs via SSH, and executes heavy lifting (model pulls, env generation).
# WHY IT EXISTS: It prepares the entire distributed cluster for work in a single invocation
#                from the Control node, eliminating manual cross-node synchronization.
setup: | $(PYTHON_BIN)
	@$(call h1_title,"INITIATING CLUSTER-WIDE METACLAW SETUP")
	@$(PYTHON_BIN) ./bin/cluster_setup.py
	@$(MAKE) --no-print-directory setup-local

# WHAT IT DOES: Evaluates local providers, generates documents, creates secrets, and pulls models for the current machine.
# WHY IT EXISTS: Separated from `setup` so that `cluster_setup.py` can invoke this target remotely on compute nodes via SSH.
setup-local: bootstrap docs | $(PYTHON_BIN)
	@echo "\n[Setup] Instantiating environment variables across all active services..."
	@$(MAKE) --no-print-directory .env
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				if [ -f "$$REAL_DIR/.metal" ] || [ -f "$$REAL_DIR/docker-compose.yml" ]; then \
					echo "Instantiating environment for $$REAL_DIR..."; \
					cd $$REAL_DIR && $(PYTHON_BIN) $(CURDIR)/bin/env_instantiate.py -v; \
					cd $(CURDIR); \
				fi; \
			fi; \
		fi; \
	done
	@echo "\n[Setup] Pre-fetching models and executing heavy lifting..."
	@if [ -L "services/runner" ] && grep -q "pull-models:" services/runner/Makefile; then \
		$(MAKE) --no-print-directory -C services/runner pull-models || true; \
	fi
	@echo "\n[Setup] Local node preparation complete."

# WHAT IT DOES: Distributes and executes wizard-batch across all nodes via SSH
# WHY IT EXISTS: Solves the chicken-and-egg deployment problem by ensuring the cluster is built sequentially.
wizard-cluster: | $(PYTHON_BIN)
	@$(call h1_title,"INITIATING DISTRIBUTED CLUSTER WIZARD")
	@$(PYTHON_BIN) ./bin/wizard_cluster.py

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
__undock:
	@for dir in $(DOCKER_SUBDIRS); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				$(call h1_title,"Executing teardown in $$REAL_DIR..."); \
				OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR down || true; \
			fi; \
		fi; \
	done

# WHAT IT DOES: Compares running container configurations against physical `.env` files and restarts/rebuilds them if mismatched.
# WHY IT EXISTS: The standard deployment command for pushing infrastructure changes gracefully.
apply: symlinks
	@$(call h1_title,"RECONCILING GLOBAL INFRASTRUCTURE STATE")
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				echo "[Root] Evaluating state in $$REAL_DIR..."; \
				$(MAKE) --no-print-directory -C $$REAL_DIR apply || true; \
			fi; \
		fi; \
	done

# WHAT IT DOES: Triggers the Python script to iterate through the cluster and report status across all nodes.
status: | $(PYTHON_BIN)
	@$(PYTHON_BIN) ./bin/cluster_status.py

# WHAT IT DOES: Executes `docker ps` for all managed containers on the local machine.
status-local:
	@$(call h1_title,"LOCAL INFRASTRUCTURE STATUS")
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				echo "--------------------------------------------------------------------------------"; \
				echo "[Root] Checking status of $$REAL_DIR..."; \
				$(MAKE) --no-print-directory -C $$REAL_DIR status || true; \
			fi; \
		fi; \
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
	@$(call h1_title,"INITIATING FRAMEWORK DEPLOYMENT")
	@if [ "$(INTERACTIVE)" = "1" ]; then \
		$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/docs/index.html"; \
	fi
	@mkdir -p .logs
	@$(call h2_title,"PRE-FLIGHT ENVIRONMENT CONFIGURATION")
	@for dir in $(WIZARD_BOOT_ORDER); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				if [ -f "$$REAL_DIR/.metal" ] || [ -f "$$REAL_DIR/docker-compose.yml" ]; then \
					if [ "$(INTERACTIVE)" = "1" ] && [ -f "$$REAL_DIR/index.md" ]; then \
						$(PYTHON_BIN) $(CURDIR)/bin/compile_md.py -i $$REAL_DIR/index.md --html; \
						$(PYTHON_BIN) ./bin/browser.py "file://$(CURDIR)/$$REAL_DIR/index.html#env.vars"; \
					fi; \
					if grep -q "prep-instructions:" $$REAL_DIR/Makefile; then \
						$(MAKE) --no-print-directory -C $$REAL_DIR prep-instructions; \
					fi; \
					if [ "$(INTERACTIVE)" = "1" ]; then \
						comp=$$(basename $$REAL_DIR); \
						printf "$$comp environment is set. Proceed? [Y/n] "; \
						read answer < /dev/tty; \
						if [ "$$answer" != "" ] && [ "$$answer" != "Y" ] && [ "$$answer" != "y" ] && [ "$$answer" != "yes" ]; then \
							echo "Setup aborted by user."; exit 1; \
						fi; \
					fi; \
				fi; \
			fi; \
		fi; \
	done
	@$(call h2_title,"DEPLOYING CLUSTER INFRASTRUCTURE")
	@for dir in $(WIZARD_BOOT_ORDER); do \
		$(call h2_title,"$$dir"); \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
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
			fi; \
		fi; \
	done
	@$(call h2_title,"APPLYING GATEWAY CONFIGURATION")
	@if [ -d "$(GATEWAY_SUBDIR)" ] && [ -f "$(GATEWAY_SUBDIR)/Makefile" ]; then \
		echo "Applying routing patch..."; \
		$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) patch; \
	else \
		echo "No Gateway plane detected on this node. Skipping routing patch."; \
	fi

	@if [ "$(INTERACTIVE)" = "1" ]; then \
		$(call h2_title,"LAUNCHING WEB GUI..."); \
		if [ -d "$(GATEWAY_SUBDIR)" ] && [ -f "$(GATEWAY_SUBDIR)/Makefile" ]; then \
			echo "Waiting for OpenClaw Gateway to finish booting..."; \
			$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) wait-healthy; \
			$(PYTHON_BIN) ./bin/browser.py --close; \
			$(MAKE) --no-print-directory -C $(GATEWAY_SUBDIR) gui-setup; \
		else \
			echo "Node deployed successfully. (No Gateway UI present on this node)."; \
			$(PYTHON_BIN) ./bin/browser.py --close >/dev/null 2>&1 || true; \
		fi; \
	else \
		echo "# BATCH WIZARD COMPLETE. ALL SYSTEMS ONLINE."; \
	fi

# ==============================================================================
# SYSTEM PURGE & RESET TARGETS
# ==============================================================================

# WHAT IT DOES: Deletes ephemeral files (`verification.log`, cached `.html` pages, `.state_*` flags) globally.
# WHY IT EXISTS: Cleans up the developer workspace without harming secrets or databases.
clean-state:
	@$(call h2_title,"CLEANING LOCAL STATE ACROSS ALL SERVICES")
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR clean-state || echo "Warning: $$REAL_DIR clean-state failed."; \
			fi; \
		fi; \
	done

# WHAT IT DOES: Triggers `factory-reset-soft` as the default reset behavior.
factory-reset: factory-reset-soft

# WHAT IT DOES: Tears down all containers, destroys the network, and wipes `.env` text files.
# WHY THIS DEFAULT: **CRITICAL** - It explicitly PRESERVES `.env.json` (your cached secrets), `profile.json`, and all persistent external data.
#   This is the safest way to bounce a broken framework.
factory-reset-soft: __undock clean-network
	@$(call h1_title,INITIATING FACTORY RESET (SOFT - PRESERVING SECRETS & DATA))
	@$(MAKE) --no-print-directory clean-state
	@$(call h2_title,"Removing .env files...")
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; elif [ -d "$$dir" ]; then REAL_DIR="$$dir"; else continue; fi; \
		rm -f "$$REAL_DIR/.env"; \
	done
	@$(call h2_title,"Purging global runtime state...")
	@rm -f .env tmp/metaclaw.txt docs/index.html .env.cluster
	@rm -rf .logs
	@$(PYTHON_BIN) ./bin/browser.py --close >/dev/null 2>&1 || true
	@find . -name "*.env.tmp" -type f -delete 2>/dev/null || true
	@echo "Soft reset complete. External data, .env.json files, profile.json, and python .venv preserved."

# WHAT IT DOES: The Nuclear Option. Destroys everything, including cached `.env.json` secrets and the hardware `profile.json`.
# WHY IT EXISTS: Required if the user wishes to redeploy from scratch with entirely new API keys or a different hardware cluster configuration.
factory-reset-hard: factory-reset-soft
	@$(call h1_title,"INITIATING FACTORY RESET (HARD - DESTROYING SECRETS & DATA)")
	@for dir in $(DOCKER_SUBDIRS) $(BARE_SUBDIRS); do \
		if [ -L "$$dir" ]; then \
			TARGET=$$(readlink "$$dir"); REAL_DIR="services/$$TARGET"; \
			if [ -f "$$REAL_DIR/Makefile" ]; then \
				OPENCLAW_SKIP_ENV=1 $(MAKE) --no-print-directory -C $$REAL_DIR clobber-data || echo "Warning: $$REAL_DIR clobber-data failed."; \
				rm -f "$$REAL_DIR/.env.json"; \
			fi; \
		fi; \
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
	@$(call h1_title,"PACKAGING FRAMEWORK")
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
	@$(call h1_title,"[GitOps] Provisioning MetaClaw repository in agent workspace...")
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
	@$(call h1_title,"[GitOps] Pulling merged updates from the public repository to the live host...")
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

# WHAT IT DOES: Concatenates the workspace agents into a single `.txt` payload for injection into an LLM context window.
wksp: tmp/workspace.txt
tmp/workspace.txt: FORCE | $(PYTHON_BIN)
	@mkdir -p tmp
	$(PYTHON_BIN) ./bin/newcode.py -s docs/WORKSPACE.files > tmp/workspace.txt
	@echo "Workspace manifest generated at: tmp/workspace.txt"
==== गुलाबी bin/cluster_setup.py <====
#!/usr/bin/env python3
import os
import sys

# Ensure sysprofile can be imported from the local bin directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import sysprofile

import json
import socket
import platform
import shutil
import subprocess

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_tailscale_active():
    """
    Checks if the Tailscale daemon is currently running on the host OS.
    """
    try:
        res = subprocess.run(['tailscale', 'status'], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def get_required_ssh_key():
    """
    Ensures the strict use of the MetaClaw deployment key.
    """
    home = os.path.expanduser("~")
    metaesque_key = os.path.join(home, ".ssh", "id_ed25519_metaesque")

    if not os.path.exists(metaesque_key):
        print(f"FATAL: Required SSH key not found at {metaesque_key}")
        print("Ensure bin/setup_plane.sh was executed properly.")
        sys.exit(1)

    return metaesque_key

def run_remote(ip_address, ssh_user, key_filename, cmd, hide=False):
    """
    Executes a remote command using the native OpenSSH client via subprocess.
    This safely bypasses Paramiko's inability to negotiate Tailscale's 'none' auth.
    """
    ssh_cmd = [
        "ssh", "-i", key_filename,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        f"{ssh_user}@{ip_address}",
        cmd
    ]
    if hide:
        return subprocess.run(ssh_cmd, capture_output=True, text=True)
    else:
        return subprocess.run(ssh_cmd)

def scp_remote(ip_address, ssh_user, key_filename, src, dst):
    """
    Transfers a file using the native SCP client.
    """
    scp_cmd = [
        "scp", "-i", key_filename,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        src,
        f"{ssh_user}@{ip_address}:{dst}"
    ]
    return subprocess.run(scp_cmd, capture_output=True, text=True)

def profile_remote_hardware(ip_address, ssh_user, key_filename):
    """
    Executes Phase 2 Interrogation via native SSH, bootstrapping the remote
    Python environment and invoking the remote sysprofile.py script.
    """
    try:
        print(f"  -> Connecting to {ssh_user}@{ip_address} via native SSH...")

        print("  -> Bootstrapping remote Python environment...")
        run_remote(ip_address, ssh_user, key_filename, "cd ~/repo && make -C bin install-code > /dev/null 2>&1", hide=True)

        print("  -> Syncing local sysprofile.py to remote node...")
        sysprofile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sysprofile.py")
        scp_remote(ip_address, ssh_user, key_filename, sysprofile_path, "repo/bin/sysprofile.py")

        print("  -> Executing remote sysprofile.py...")
        # Use a python one-liner over SSH to import the remote sysprofile module and dump the dict
        cmd = """cd ~/repo && bin/.venv/bin/python -c "import sys; sys.path.insert(0, 'bin'); import sysprofile; import json; print(json.dumps(sysprofile.platform_details()))" """
        res = run_remote(ip_address, ssh_user, key_filename, cmd, hide=True)

        if res.returncode != 0:
            raise Exception(res.stderr.strip())

        hw_details = json.loads(res.stdout.strip())
        return hw_details

    except Exception as e:
        print(f"  -> FATAL: Remote interrogation failed: {e}")
        print("  -> Falling back to default baseline estimations.")
        return {
            "os": "Linux",
            "architecture": "x86_64",
            "ip_address": ip_address,
            "tailscale_active": True
        }

def get_tailscale_ip(target_hostname):
    """
    Executes 'tailscale status --json' and parses the output to dynamically
    find the Tailscale IP address associated with the requested hostname.
    """
    try:
        res = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        for peer_key, peer_info in data.get('Peer', {}).items():
            host = peer_info.get('HostName', '')
            if host.lower() == target_hostname.lower():
                ips = peer_info.get('TailscaleIPs', [])
                if ips:
                    return ips[0]

        self_info = data.get('Self', {})
        if self_info.get('HostName', '').lower() == target_hostname.lower():
            ips = self_info.get('TailscaleIPs', [])
            if ips:
                return ips[0]

    except Exception:
        pass

    return ""

def configure_env_secrets(profile, ssh_key=None):
    """
    Phase 4: Establishes global secrets locally, then uses SSH and jq to safely
    merge them into the remote nodes' .env.json files without destroying local overrides.
    """
    print("\n[Phase 4] Configuring Global Secrets (.env.json)...")
    import secrets
    import string

    def gen_pwd():
        return "sk-" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

    litellm_env_dir = os.path.join("services", "proxies", "litellm")
    local_env_json = os.path.join(litellm_env_dir, ".env.json")

    env_data = {}
    if os.path.exists(local_env_json):
        try:
            with open(local_env_json, "r") as f:
                env_data = json.load(f)
        except:
            pass

    active_key = env_data.get("ACTIVE_PROXY_KEY")
    gemini_key = env_data.get("GEMINI_API_KEY", "")

    if not active_key or "change_me" in active_key:
        active_key = gen_pwd()
        print(f"  -> Generated new ACTIVE_PROXY_KEY: {active_key}")
    else:
        print("  -> ACTIVE_PROXY_KEY already exists. Preserving.")

    gemini_input = input(f"  -> Enter GEMINI_API_KEY [{gemini_key or 'None'}]: ").strip()
    if gemini_input:
        gemini_key = gemini_input

    env_data["ACTIVE_PROXY_KEY"] = active_key
    env_data["GEMINI_API_KEY"] = gemini_key

    os.makedirs(litellm_env_dir, exist_ok=True)
    with open(local_env_json, "w") as f:
        json.dump(env_data, f, indent=2)

    # Broadcast secrets to other nodes via jq merging
    for node in profile.get("nodes", []):
        if node["hostname"] != socket.gethostname() and node.get("tier") == 2:
            ip = node["hardware"]["ip_address"]
            user = node.get("ssh_user", os.getlogin())
            print(f"  -> Pushing secrets to {node['hostname']} ({ip})...")

            # This complex jq string safely creates the file if missing, then merges the keys
            jq_cmd = f"mkdir -p ~/repo/services/proxies/litellm && " \
                     f"touch ~/repo/services/proxies/litellm/.env.json && " \
                     f"jq -n 'inputs | .ACTIVE_PROXY_KEY=\"{active_key}\" | .GEMINI_API_KEY=\"{gemini_key}\"' " \
                     f"~/repo/services/proxies/litellm/.env.json > ~/repo/tmp_env.json 2>/dev/null || " \
                     f"echo '{{\"ACTIVE_PROXY_KEY\":\"{active_key}\",\"GEMINI_API_KEY\":\"{gemini_key}\"}}' > ~/repo/tmp_env.json && " \
                     f"mv ~/repo/tmp_env.json ~/repo/services/proxies/litellm/.env.json"

            res = run_remote(ip, user, ssh_key, jq_cmd, hide=True)
            if res.returncode != 0:
                print(f"  -> WARNING: Failed to push secrets. Is jq installed on the remote host? Error: {res.stderr}")

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Setup Engine")
    print("==================================================")

    # 1. Profile the local orchestrating node
    local_host = socket.gethostname()
    local_hw = sysprofile.platform_details()

    print(f"\n[Master] Profiling orchestrator node '{local_host}'...")
    print(f"  IP Address: {local_hw['ip_address']}")
    print(f"  OS RAM capacity: {local_hw['ram_gb']} GB")
    print(f"  Hardware RAM detected: {local_hw.get('ram_hardware_gb')} GB")
    print(f"  Native Tailscale Active: {local_hw.get('tailscale_active', False)}")

    # Explicit headless prompt to defeat dummy plug heuristics
    default_hl = 'y' if local_hw.get('tailscale_active') else 'n'
    hl_input = input(f"Is orchestrator node '{local_host}' running headless? [{default_hl}]: ").strip().lower()
    local_hw['headless'] = True if hl_input in ['y', 'yes'] else (False if hl_input in ['n', 'no'] else default_hl == 'y')

    print("\nConfigure Cluster Topology:")
    print("  [0] Tier 0: Single Laptop Minilith (Constrained Context)")
    print("  [1] Tier 1: Single Mini-PC Monolith (All-In-One Node)")
    print("  [2] Tier 2: Data Sovereignty Farm (Split Control + Compute Nodes)")

    while True:
        tier_choice = input("Select cluster architecture [0]: ").strip() or "0"
        if tier_choice in ["0", "1", "2"]:
            break
        print("Invalid allocation tier choice.")

    profile = {
        "cluster_id": f"metaclaw-cluster-centralized",
        "routing_strategy": "lexical_predictive",
        "nodes": []
    }

    ssh_key = None
    if tier_choice == "2":
        profile["nodes"].append({
            "hostname": local_host,
            "tier": 2,
            "planes": ["control", "execution", "archive"],
            "require_wan": True,
            "ssh_user": os.getlogin(),
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })

        print("\nEnter remote Compute node network coordinates:")
        compute_host = input("Compute Node Hostname [compute]: ").strip() or "compute"

        default_ip = get_tailscale_ip(compute_host)
        ip_prompt = f"Compute Node IP address [{default_ip}]: " if default_ip else "Compute Node IP address (e.g., 100.x.y.z): "
        compute_ip = input(ip_prompt).strip()
        if not compute_ip and default_ip:
            compute_ip = default_ip

        current_user = os.getlogin()
        ssh_user = input(f"SSH Username for remote connection [{current_user}]: ").strip() or current_user

        ssh_key = get_required_ssh_key()
        print(f"Using enforced SSH identity: {ssh_key}")

        print(f"\n[Phase 2] Executing remote hardware interrogation on {compute_host}...")
        compute_hw = profile_remote_hardware(compute_ip, ssh_user, ssh_key)

        print(f"\n[Hardware Verification] Node: {compute_host}")
        print(f"  Detected OS RAM: {compute_hw.get('ram_gb')} GB")
        print(f"  Detected Hardware RAM: {compute_hw.get('ram_hardware_gb')} GB")
        print(f"  Detected GPU: {compute_hw.get('gpu_detected')}")

        # CRITICAL FIX: Overwrite the hardware IP returned by sysprofile (which is the LAN IP)
        # with the explicitly resolved Tailscale IP, so all downstream orchestration uses Tailscale SSH.
        compute_hw['ip_address'] = compute_ip

        c_default_hl = 'y' if compute_hw.get('tailscale_active') else 'y'
        c_hl_input = input(f"Is Compute node '{compute_host}' running headless? [{c_default_hl}]: ").strip().lower()
        compute_hw['headless'] = True if c_hl_input in ['y', 'yes'] else (False if c_hl_input in ['n', 'no'] else c_default_hl == 'y')

        profile["nodes"].append({
            "hostname": compute_host,
            "tier": 2,
            "planes": ["compute"],
            "require_wan": True,
            "ssh_user": ssh_user,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": compute_hw
        })
    else:
        profile["nodes"].append({
            "hostname": local_host,
            "tier": int(tier_choice),
            "planes": ["control", "compute", "execution", "archive"],
            "require_wan": False,
            "ssh_user": os.getlogin(),
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
    import metaclaw

    profile = metaclaw.Inst.updateCluster(
        profile, local_host, int(tier_choice),
        profile["nodes"][0]["planes"], local_hw,
        True if tier_choice == "2" else False, local_hw['headless'], ["cost", "safety", "resources"]
    )

    with open("profile.json", "w") as f:
        json.dump(profile, f, indent=2)

    print("\nSUCCESS: Idempotent profile.json compiled successfully.")

    # --- PHASE 3: Broadcast ---
    if tier_choice == "2":
        print(f"\n[Phase 3] Broadcasting unified profile.json to cluster nodes...")
        res = scp_remote(compute_ip, ssh_user, ssh_key, "profile.json", "repo/profile.json")
        if res.returncode == 0:
            print(f"  -> Successfully pushed to {compute_host}.")
        else:
            print(f"  -> WARNING: Failed to push profile.json: {res.stderr}")
            print("  -> Run 'make sync-cluster' manually.")

    # --- PHASE 4: Global Secrets ---
    configure_env_secrets(profile, ssh_key)

    # --- PHASE 5: Remote Execution Pipeline ---
    print("\n[Phase 5] Executing remote cluster setup tasks...")
    for node in profile.get("nodes", []):
        if node["hostname"] != socket.gethostname():
            ip = node["hardware"]["ip_address"]
            user = node.get("ssh_user", os.getlogin())
            print(f"  -> Triggering 'make setup-local' on remote node {node['hostname']} ({ip})...")
            # Using run_remote with hide=False streams the exact execution output (like model pulling progress)
            # directly back to the human user's local terminal so they are not left in the dark.
            res = run_remote(ip, user, ssh_key, "cd ~/repo && make setup-local", hide=False)
            if res.returncode != 0:
                print(f"  -> WARNING: Remote setup failed on {node['hostname']}.")

    print("\nCluster configuration complete. Proceed by running: make wizard-cluster")

if __name__ == "__main__":
    main()
