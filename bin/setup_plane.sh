#!/bin/bash
# ==============================================================================
# MetaClaw: Headless Node Bootstrapper
# ==============================================================================
# This script initializes a sterile, headless Ubuntu Server node. It installs
# critical OS dependencies, sets the hostname, generates GitHub deployment keys,
# clones the framework repository, installs Docker, and installs Tailscale.
#
# NEW FEATURE: This script now acts as its own deployment orchestrator.
# You can run it locally from your laptop to push the installation to a remote node.

set -e

SCRIPT_PATH=$(readlink -f "$0")

# ==============================================================================
# MODE 1: LOCAL DEPLOYMENT ORCHESTRATOR
# Executed from laptop: ./bin/setup_plane.sh --deploy user@192.168.1.50 spark2
# ==============================================================================
if [ "$1" == "--deploy" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: ./bin/setup_plane.sh --deploy <ssh-user>@<local-ip> <new-hostname>"
        echo "Example: ./bin/setup_plane.sh --deploy wade@192.168.0.105 spark2"
        exit 1
    fi
    TARGET="$2"
    NEW_HOSTNAME="$3"

    echo "################################################################################"
    echo "# METACLAW REMOTE DEPLOYMENT ORCHESTRATOR"
    echo "################################################################################"
    echo "[1/4] Copying bootstrap script to $TARGET..."
    scp "$SCRIPT_PATH" "$TARGET:/tmp/setup_plane.sh"

    echo "\n[2/4] Executing Phase 1 (Pre-Docker Setup) on $TARGET..."
    # Execute Phase 1 remotely
    ssh -t "$TARGET" "bash /tmp/setup_plane.sh --phase1 $NEW_HOSTNAME"

    echo "\n[3/4] Connection gracefully dropped to refresh Docker group permissions."
    echo "      Reconnecting to execute Phase 2 (Tailscale Integration)..."
    ssh -t "$TARGET" "bash /tmp/setup_plane.sh --phase2"

    echo "\n################################################################################"
    echo "# DEPLOYMENT TO $NEW_HOSTNAME COMPLETE"
    echo "################################################################################"
    read -p "Would you like to SSH into your Control Node now to run 'make setup'? [y/N]: " ssh_choice
    if [[ "$ssh_choice" =~ ^[Yy]$ ]]; then
        read -p "Enter Control Node SSH address (e.g., metaclaw@control): " control_target
        echo "Connecting to Control Node..."
        ssh -t "$control_target" "cd ~/repo && make setup"
    else
        echo "Exiting orchestrator. Remember to run 'make setup' on your Control Node later to register the new Compute node."
    fi
    exit 0
fi

# ==============================================================================
# MODE 2: REMOTE PHASE 1 (Host Config, Repos, Docker)
# ==============================================================================
if [ "$1" == "--phase1" ]; then
    NEW_HOSTNAME="$2"
    if [ -z "$NEW_HOSTNAME" ]; then
        echo "Error: Hostname must be provided for Phase 1."
        exit 1
    fi

    echo "################################################################################"
    echo "# PHASE 1: SYSTEM INITIALIZATION"
    echo "################################################################################"

    echo "[*] Setting system hostname to '$NEW_HOSTNAME'..."
    sudo hostnamectl set-hostname "$NEW_HOSTNAME"
    # Update /etc/hosts to prevent sudo resolution hangs
    if grep -q "127.0.1.1" /etc/hosts; then
        sudo sed -i "s/^127.0.1.1.*/127.0.1.1       $NEW_HOSTNAME/g" /etc/hosts
    else
        echo "127.0.1.1       $NEW_HOSTNAME" | sudo tee -a /etc/hosts
    fi

    echo "[*] Installing core system dependencies..."
    sudo apt-get update
    sudo apt-get install -y make python3-venv python3-pip git curl netcat-openbsd jq

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
    fi

    REPO_DIR="$HOME/repo"
    if [ ! -d "$REPO_DIR" ]; then
        echo "[*] Cloning MetaClaw repository..."
        ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
        git clone git@metaesque.ssh:metaesque/metaclaw.git "$REPO_DIR"
    else
        echo "[*] Repository directory already exists at $REPO_DIR. Skipping clone."
    fi

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
    fi

    # DGX Spark / GB10 Superchip Specific Overrides
    if [ -f /etc/os-release ] && grep -qi "dgx" /etc/os-release; then
        echo "[*] NVIDIA DGX OS detected. Applying Superchip ecosystem overrides..."

        echo "  -> Masking sleep/hibernation targets to prevent offline model eviction..."
        sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

        echo "  -> Enforcing iptables-legacy for Docker bridge network compatibility..."
        sudo apt-get install -y iptables
        sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
        sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

        if command -v nvidia-ctk >/dev/null 2>&1; then
            echo "  -> Configuring Docker to utilize NVIDIA Container Toolkit..."
            sudo nvidia-ctk runtime configure --runtime=docker || true
        fi
    fi

    echo "[*] Executing make install-docker..."
    cd "$REPO_DIR" && make install-docker

    echo "Phase 1 complete. Disconnecting."
    exit 0
fi

# ==============================================================================
# MODE 3: REMOTE PHASE 2 (Tailscale)
# ==============================================================================
if [ "$1" == "--phase2" ]; then
    echo "################################################################################"
    echo "# PHASE 2: OVERLAY NETWORK INITIALIZATION"
    echo "################################################################################"

    if ! command -v tailscale >/dev/null 2>&1; then
        echo "[*] Installing Tailscale..."
        curl -fsSL https://tailscale.com/install.sh | sh
    else
        echo "[*] Tailscale is already installed."
    fi

    echo "[*] Authenticating node to the mesh network..."
    sudo tailscale up --ssh

    echo "Phase 2 complete."
    exit 0
fi

echo "Please run this script with --deploy <ssh-user>@<local-ip> <new-hostname> from your laptop to orchestrate deployment."
exit 1
