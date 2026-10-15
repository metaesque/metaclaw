SERVICE_TITLE = Ollama Runner Service
# Ollama is host-native, not dockerized, so SERVICE_NAME is N/A, but we set it for completeness
SERVICE_NAME = ollama-runner

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
# ARCHITECTURAL SHIFT: Depend on the abstracted gateway symlink instead of hardcoding openclaw-gateway
-include $(FRAMEWORK_ROOT)/services/gateway/.env
# ARCHITECTURAL SHIFT: Include proxy variables to dynamically detect which models to pull
-include $(FRAMEWORK_ROOT)/services/proxy/.env
export

PID_FILE = .ollama.pid
LOG_FILE = ollama.log

.PHONY: up down status models clean-state clobber-data check-status check-logs wait-healthy pull-models apply docs

up:: ./bin/ollama
	@set -a; \
	[ -f "$(FRAMEWORK_ROOT)/.env" ] && . "$(FRAMEWORK_ROOT)/.env"; \
	[ -f ".env" ] && . "./.env"; \
	set +a; \
	PORT_VAL="$${OLLAMA_PORT:-11434}"; \
	if [ "$$(uname -s)" = "Linux" ] && command -v sudo >/dev/null 2>&1 && command -v iptables >/dev/null 2>&1; then \
		sudo iptables -C INPUT -p tcp -s 172.16.0.0/12 --dport "$$PORT_VAL" -j ACCEPT 2>/dev/null || \
		sudo iptables -I INPUT 1 -p tcp -s 172.16.0.0/12 --dport "$$PORT_VAL" -j ACCEPT 2>/dev/null || true; \
	fi; \
	if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is already running (PID: $$(cat $(PID_FILE)))" ; \
	else \
		echo "Cleaning up any orphaned processes before boot..." ; \
		$(MAKE) --no-print-directory down ; \
		echo "Starting Ollama natively..." ; \
		HOST_BIND="$${OLLAMA_HOST:-0.0.0.0}:$$PORT_VAL"; \
		MODELS_DIR="$${EXTERNAL_DRIVE_PATH:-$(FRAMEWORK_ROOT)/external/metaclaw}/ollama-models"; \
		mkdir -p "$$MODELS_DIR"; \
		OLLAMA_HOST="$$HOST_BIND" OLLAMA_KEEP_ALIVE="$${OLLAMA_KEEP_ALIVE:-60m}" OLLAMA_VULKAN="$$OLLAMA_VULKAN" OLLAMA_IGPU_ENABLE="$$OLLAMA_IGPU_ENABLE" ROCR_VISIBLE_DEVICES="$$ROCR_VISIBLE_DEVICES" OLLAMA_MODELS="$$MODELS_DIR" nohup ./bin/ollama serve > $(LOG_FILE) 2>&1 < /dev/null & \
		echo $$! > $(PID_FILE) ; \
	fi
	@$(MAKE) --no-print-directory pull-models

down::
	@echo "Stopping Ollama..."
	@if [ -f $(PID_FILE) ]; then \
		kill $$(cat $(PID_FILE)) 2>/dev/null || true ; \
		rm -f $(PID_FILE) ; \
	fi
	@PORT_VAL="$${OLLAMA_PORT:-11434}"; \
	ORPHAN=$$(lsof -t -i TCP:$$PORT_VAL 2>/dev/null) ; \
	if [ -n "$$ORPHAN" ]; then \
		echo "Force killing orphaned process on port $$PORT_VAL (PID: $$ORPHAN)..." ; \
		kill -9 $$ORPHAN 2>/dev/null || true ; \
	fi

status::
	@if [ -f $(PID_FILE) ] && ps -p $$(cat $(PID_FILE)) > /dev/null; then \
		echo "Ollama is RUNNING." ; \
	else \
		echo "Ollama is STOPPED." ; \
	fi

models:
	@if [ -x "./bin/ollama" ]; then \
		PORT_VAL="$${OLLAMA_PORT:-11434}"; \
		echo "=== Installed Ollama Models on $$(hostname) ==="; \
		OLLAMA_HOST=127.0.0.1:$$PORT_VAL ./bin/ollama list 2>/dev/null || echo "Ollama daemon is not responding on port $$PORT_VAL."; \
		echo ""; \
		echo "=== Active Models in VRAM (ollama ps) on $$(hostname) ==="; \
		OLLAMA_HOST=127.0.0.1:$$PORT_VAL ./bin/ollama ps 2>/dev/null || true; \
	else \
		echo "Ollama binary not installed on $$(hostname)."; \
	fi

check-logs::
	@echo "[$(SERVICE_TITLE)] Tailing last 5 lines of $(LOG_FILE)..."
	@tail -n 5 $(LOG_FILE) 2>/dev/null || echo "Log file not found."

check-status:: status
	@echo "================================================================================"
	@echo "= $(SERVICE_TITLE) INTEGRITY VERIFICATION"
	@echo "================================================================================"
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Responsiveness ---" > verification.log
	@PORT_VAL="$${OLLAMA_PORT:-11434}"; \
	curl -s http://127.0.0.1:$$PORT_VAL/api/tags | $(PYTHON_BIN) -c "import sys, json; data=json.load(sys.stdin); print(f'Models Loaded: {len(data.get(\"models\", []))}')" 2>/dev/null >> verification.log || echo "API unreachable." >> verification.log
	@if grep -q "API unreachable" verification.log; then echo "FATAL: Ollama API unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "Models Loaded:"

clean-state:: down
	@echo "Scrubbing local runtime state..."
	@rm -f $(LOG_FILE) $(PID_FILE) verification.log index.html .updated

clobber-data:
	@if [ -n "$(EXTERNAL_DRIVE_PATH)" ]; then \
		echo "Purging Ollama models from external drive..." ; \
		rm -rf $(EXTERNAL_DRIVE_PATH)/ollama-models ; \
	fi

# Root reconciliation integration
apply:: .env
	@echo "[$(SERVICE_TITLE)] Reconciling state..."
	@chmod +x install.sh
	@rm -f .updated
	@./install.sh
	@echo "[$(SERVICE_TITLE)] Bouncing daemon to apply new configuration..."
	@$(MAKE) --no-print-directory down
	@rm -f .updated
	@$(MAKE) --no-print-directory up

./bin/ollama:
	@echo "Downloading Ollama binary via install.sh..."
	@mkdir -p ./bin
	@chmod +x install.sh
	@./install.sh

wait-healthy:: status
	@echo "[$(SERVICE_TITLE)] Awaiting healthy state..."
	@PORT_VAL="$${OLLAMA_PORT:-11434}"; \
	attempt=1; \
	while [ $$attempt -le 30 ]; do \
		if curl -s http://127.0.0.1:$$PORT_VAL/api/tags > /dev/null; then \
			echo "[$(SERVICE_TITLE)] Status: HEALTHY."; \
			exit 0; \
		fi; \
		echo "[$(SERVICE_TITLE)] Status: starting. Retrying in 2s ($$attempt/30)..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	echo "FATAL: [$(SERVICE_TITLE)] Failed to reach healthy state."; \
	cat $(LOG_FILE) 2>/dev/null || true; \
	exit 1

# Instructs the running Ollama process to pull any models assigned to it by the global orchestrator configuration.
# Streams live progress from the local Ollama HTTP API with percentage, GB transferred, MB/s speed, ETA, and total elapsed time.
pull-models: wait-healthy
	@echo "[$(SERVICE_TITLE)] Validating and pulling assigned local models..."
	@$(PYTHON_BIN) -c 'import os, re, sys, time, urllib.request, json; \
	from dotenv import dotenv_values; \
	cfg = {}; \
	[cfg.update(dotenv_values(p)) for p in ["$(FRAMEWORK_ROOT)/.env", ".env", "$(FRAMEWORK_ROOT)/services/gateway/.env"] if os.path.exists(p)]; \
	port = cfg.get("OLLAMA_PORT") or "11434"; \
	keep_alive = cfg.get("OLLAMA_KEEP_ALIVE") or "60m"; \
	raw_str = (cfg.get("OLLAMA_TARGET_MODELS") or "") + " " + (cfg.get("OPENCLAW_JUDGE_MODEL") or ""); \
	tokens = [re.sub(r"^ollama(_chat)?/", "", t.strip("\"\x27 ")) for t in raw_str.split()]; \
	models = list(dict.fromkeys([m for m in tokens if m and m != "judge-model" and not m.startswith("gemini/")])); \
	def pull_one(m): \
	    t0 = time.time(); \
	    print(f"  -> Pulling {m}...", flush=True); \
	    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/pull", data=json.dumps({"name": m, "stream": True}).encode(), headers={"Content-Type": "application/json"}); \
	    try: \
	        resp = urllib.request.urlopen(req, timeout=3600); \
	        last_print = 0.0; \
	        for raw_line in resp: \
	            evt = json.loads(raw_line.decode("utf-8", errors="ignore")); \
	            status = evt.get("status", ""); \
	            total = evt.get("total", 0); \
	            comp = evt.get("completed", 0); \
	            now = time.time(); \
	            if total > 0 and (now - last_print >= 0.25 or comp == total): \
	                last_print = now; \
	                pct = (comp / total) * 100.0; \
	                el = max(0.001, now - t0); \
	                spd = (comp / (1024*1024)) / el; \
	                rem = ((total - comp) / (comp / el)) if comp > 0 else 0; \
	                bar_w = 24; \
	                filled = int(bar_w * comp // total); \
	                bar = "#" * filled + "-" * (bar_w - filled); \
	                sys.stdout.write(f"\r     [{bar}] {pct:5.1f}% ({comp/(1024**3):.2f}/{total/(1024**3):.2f} GB) | {spd:5.1f} MB/s | ETA: {int(rem)}s   "); \
	                sys.stdout.flush(); \
	        el_total = time.time() - t0; \
	        sys.stdout.write(f"\n     Done: {m} verified/pulled in {el_total:.1f}s.\n"); \
	        sys.stdout.flush(); \
	    except Exception as e: \
	        print(f"\nWARNING: Failed to pull {m}: {e}", flush=True); \
	[pull_one(m) for m in models]; \
	(print("  -> Pre-warming gemma4:e4b into memory...", flush=True), urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/generate", data=json.dumps({"model": "gemma4:e4b", "prompt": "", "keep_alive": keep_alive}).encode(), headers={"Content-Type": "application/json"}), timeout=60)) if "gemma4:e4b" in models else None'
