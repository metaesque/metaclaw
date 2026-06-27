#!/usr/bin/env bash

# Enforce strict error handling
# -e: exit on command failure
# -u: exit on unbound variable
# -o pipefail: exit if any command in a pipeline fails
set -euo pipefail

echo "################################################################################"
echo "# MetaClaw Node Bootstrapper"
echo "# Target: Headless Control/Compute Planes"
echo "################################################################################"

# Define core variables
EMAIL="wade@holst.ca"
GIT_NAME="Wade Holst"
SSH_KEY_PATH="$HOME/.ssh/id_ed25519_metaesque"
REPO_URL="git@metaesque.ssh:metaesque/metaclaw.git"
TARGET_DIR="$HOME/workspace/src/metaclaw"

# ------------------------------------------------------------------------------
# 1. SSH Identity Generation
# ------------------------------------------------------------------------------
echo -e "\n[1/6] Validating SSH Identity..."

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [[ -f "$SSH_KEY_PATH" ]]; then
    echo "SSH key already exists at $SSH_KEY_PATH. Skipping generation."
else
    echo "Generating new Ed25519 SSH key..."
    # -t ed25519: modern secure algorithm
    # -C: comment/label
    # -f: output file location
    # -N "": empty passphrase for frictionless automated operations
    ssh-keygen -t ed25519 -C "$EMAIL" -f "$SSH_KEY_PATH" -N ""
    echo "SSH key generated successfully."
fi

# ------------------------------------------------------------------------------
# 2. GitHub Public Key Registration (Interactive)
# ------------------------------------------------------------------------------
echo -e "\n[2/6] GitHub Authentication Setup"
echo "================================================================================"
echo "ACTION REQUIRED: You must register this node's public key with your GitHub account."
echo "1. Copy the entirety of the SSH key printed below."
echo "2. Open a browser on your local machine and go to: https://github.com/settings/ssh/new"
echo "3. Title the key appropriately (e.g., 'K8 Plus Control Node' or 'EVO-X2 Compute')."
echo "4. Paste the key into the 'Key' field and click 'Add SSH key'."
echo "================================================================================"
echo ""
cat "${SSH_KEY_PATH}.pub"
echo ""
echo "================================================================================"

# Pause execution until the user explicitly confirms completion
read -p "Press [Enter] ONLY AFTER you have successfully added the key to GitHub... "

# ------------------------------------------------------------------------------
# 3. SSH Configuration Routing
# ------------------------------------------------------------------------------
echo -e "\n[3/6] Configuring SSH Host Routing..."

SSH_CONFIG="$HOME/.ssh/config"
touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"

# Check if the alias already exists to prevent duplicate entries
if grep -q "Host metaesque.ssh" "$SSH_CONFIG"; then
    echo "Host alias 'metaesque.ssh' already exists in $SSH_CONFIG. Skipping."
else
    echo "Injecting 'metaesque.ssh' alias into $SSH_CONFIG..."
    cat <<EOF >> "$SSH_CONFIG"

# MetaClaw Public Repository Routing
Host metaesque.ssh
    HostName github.com
    User git
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes
EOF
    echo "SSH routing configured."
fi

# ------------------------------------------------------------------------------
# 4. Git Global Configuration
# ------------------------------------------------------------------------------
echo -e "\n[4/6] Setting Global Git Parameters..."

git config --global user.name "$GIT_NAME"
git config --global user.email "$EMAIL"
git config --global init.defaultBranch main

echo "Git identity set to: $GIT_NAME <$EMAIL>"

# ------------------------------------------------------------------------------
# 5. Clone Repository
# ------------------------------------------------------------------------------
echo -e "\n[5/6] Cloning MetaClaw Repository..."

mkdir -p "$HOME/workspace/src"
cd "$HOME/workspace/src"

if [[ -d "$TARGET_DIR" ]]; then
    echo "Directory $TARGET_DIR already exists. Skipping clone."
else
    echo "Cloning from $REPO_URL..."
    # The clone relies on the SSH alias established in step 3 to authenticate
    # using the newly generated key, bypassing any generic github.com keys.
    git clone "$REPO_URL"
fi

# ------------------------------------------------------------------------------
# 6. Hydrate Local State
# ------------------------------------------------------------------------------
echo -e "\n[6/6] Hydrating Local Workspace State..."

cd "$TARGET_DIR"

if [[ -d "workspace" ]]; then
    echo "Local 'workspace' directory already exists. Skipping template copy."
else
    if [[ -d "workspace_template" ]]; then
        echo "Copying 'workspace_template' to 'workspace'..."
        cp -r workspace_template workspace
    else
        echo "WARNING: 'workspace_template' not found in repo. Cannot hydrate."
    fi
fi

echo -e "\n################################################################################"
echo "# Setup Complete."
echo "#"
echo "# NEXT STEPS:"
echo "# 1. Manually transfer your private .env.json and profile.json to $TARGET_DIR"
echo "# 2. Run 'make wizard-batch' to initialize the MetaClaw environment."
echo "################################################################################"
