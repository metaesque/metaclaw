.PHONY: install-code clean

# The default target ensures the .venv is bootstrapped and dependencies are met.
# It delegates to a stamp file so pip doesn't spam the terminal on every make run.
install-code: .venv/.installed

# Stamp file rule: only executes if requirements.txt is modified (or .venv is missing).
.venv/.installed: requirements.txt
	@echo "################################################################################"
	@echo "# BOOTSTRAPPING ISOLATED PYTHON ENVIRONMENT"
	@echo "################################################################################"
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt
	@echo "Installing Playwright Chromium dependencies (this may take a moment)..."
	.venv/bin/playwright install chromium
	@touch .venv/.installed

clean:
	rm -rf .venv
