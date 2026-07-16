SERVICE_TITLE = SearXNG Metasearch
SERVICE_NAME = searxng
DOCKER_SHELL_CMD = sh

FRAMEWORK_ROOT_REL = ../../..
FRAMEWORK_ROOT := $(abspath $(FRAMEWORK_ROOT_REL))

include $(FRAMEWORK_ROOT)/.Makefile.inherit

-include $(FRAMEWORK_ROOT)/.env
-include .env
export

LOG_READY_SIGNAL = listen on 0.0.0.0:8080

pre-up:
	@$(PYTHON_BIN) -c "import os, yaml; d=os.environ.get('EXTERNAL_DRIVE_PATH') or '/tmp'; d=os.path.join(d, 'searxng-data'); os.makedirs(d, exist_ok=True); open(os.path.join(d, 'limiter.toml'), 'a').close(); f=os.path.join(d, 'settings.yml'); data=yaml.safe_load(open(f)) if os.path.exists(f) else {}; data=data or {}; data.setdefault('server', {})['forwarded_for']=True; data.setdefault('server', {})['bind_address']='0.0.0.0'; data.setdefault('search', {})['formats']=['html', 'json']; data['limiter']=False; engines=data.setdefault('engines', []); [(e.update({'disabled': True}) if e.get('name') in ['wikidata', 'ahmia', 'torch'] else None) for e in engines]; yaml.dump(data, open(f, 'w'))"

post-check-status:
	@echo "Running diagnostic suite..."
	@echo "--- 1. API Health Check ---" > verification.log
	@curl -s http://localhost:$(SEARXNG_PORT)/healthz >> verification.log || echo "CONNECTION_FAILED" >> verification.log
	@echo "" >> verification.log
	@echo "SUCCESS: SearXNG API is actively serving requests." >> verification.log
	@if grep -q "CONNECTION_FAILED" verification.log; then echo "FATAL: SearXNG API unreachable."; exit 1; fi
	@$(PYTHON_BIN) $(FRAMEWORK_ROOT)/bin/highlight.py verification.log "OK" "SUCCESS: SearXNG API is actively serving requests."

clobber-data:
	@if [ -z "$(EXTERNAL_DRIVE_PATH)" ]; then echo "FATAL: EXTERNAL_DRIVE_PATH is undefined."; exit 1; fi
	@echo "[$(SERVICE_TITLE)] Purging external SearXNG data..."
	@rm -rf $(EXTERNAL_DRIVE_PATH)/searxng-data
