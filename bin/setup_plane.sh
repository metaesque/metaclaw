#!/bin/bash
# ==============================================================================
# MetaClaw: Headless Node Bootstrapper
# ==============================================================================
# This script initializes a sterile, headless Ubuntu Server node. It installs
# critical OS dependencies, generates GitHub deployment keys, and clones the
# framework repository so that `make setup` can take over.

set -e

echo "################################################################################"
echo "# METACLAW HEADLESS NODE BOOTSTRAPPER"
echo "################################################################################"

# 1. System Dependencies
# Ubuntu Server Minimal strips make and python3-venv to reduce attack surface.
# We must inject them before we can execute any Makefile targets.
# jq is required for securely parsing and merging .env.json payloads over SSH.
echo "[*] Installing core system dependencies..."
sudo apt-get update
sudo apt-get install -y make python3-venv python3-pip git curl netcat-openbsd jq

# 2. SSH Identity Generation
KEY_PATH="$HOME/.ssh/id_ed25519_metaesque"

if [ ! -f "$KEY_PATH" ]; then
    echo "[*] Generating dedicated SSH deployment key for MetaClaw..."
    ssh-keygen -t ed25519 -C "headless-node@metaclaw.cluster" -f "$KEY_PATH" -N ""

    echo "================================================================================"
    echo "ACTION REQUIRED: Add the following public key to your GitHub account."
    echo "Settings -> SSH and GPG keys -> New SSH key"
    echo "================================================================================"
    cat "${KEY_PATH}.pub"
    echo "================================================================================"
    read -p "Press Enter to continue AFTER you have added the key to GitHub..."
else
    echo "[*] SSH key already exists at $KEY_PATH. Skipping generation."
fi

# 3. SSH Config Routing
SSH_CONFIG="$HOME/.ssh/config"
if ! grep -q "Host metaesque.ssh" "$SSH_CONFIG" 2>/dev/null; then
    echo "[*] Injecting metaesque.ssh routing into ~/.ssh/config..."
    mkdir -p "$HOME/.ssh"
    cat <<EOF >> "$SSH_CONFIG"

# MetaClaw Public Repository Routing
Host metaesque.ssh
    HostName github.com
    User git
    IdentityFile $KEY_PATH
    IdentitiesOnly yes
EOF
    chmod 600 "$SSH_CONFIG"
else
    echo "[*] SSH routing block already exists. Skipping."
fi

# 4. Clone Repository
REPO_DIR="$HOME/repo"
if [ ! -d "$REPO_DIR" ]; then
    echo "[*] Cloning MetaClaw repository..."
    # Force GitHub's host key into known_hosts to prevent interactive prompts breaking the script
    ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
    git clone git@metaesque.ssh:metaesque/metaclaw.git "$REPO_DIR"
else
    echo "[*] Repository directory already exists at $REPO_DIR. Skipping clone."
fi

# 5. Swapfile Provisioning (Required for Tier 2 Compute Nodes)
SWAP_FILE="/swapfile"
if ! swapon --show | grep -q "^${SWAP_FILE}"; then
    echo "[*] Provisioning 32GB swapfile for massive LLM loading..."
    sudo fallocate -l 32G ${SWAP_FILE} 2>/dev/null || sudo dd if=/dev/zero of=${SWAP_FILE} bs=1G count=32 status=progress
    sudo chmod 600 ${SWAP_FILE}
    sudo mkswap ${SWAP_FILE}
    sudo swapon ${SWAP_FILE}
    if ! grep -q "${SWAP_FILE}" /etc/fstab; then
        echo "${SWAP_FILE} none swap sw 0 0" | sudo tee -a /etc/fstab
    fi
    echo "[*] Swapfile provisioning complete."
else
    echo "[*] Swapfile already provisioned. Skipping."
fi

echo "################################################################################"
echo "# BOOTSTRAP COMPLETE"
echo "################################################################################"
echo "Next Steps:"
echo "1. cd ~/repo"
echo "2. make install-docker (Remember to log out and log back in after!)"
echo "3. make setup"
