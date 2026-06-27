#!/usr/bin/env bash
set -e

echo "Detecting operating system..."
OS="$(uname -s)"

case "${OS}" in
    Linux*)
        if command -v docker >/dev/null 2>&1; then
            echo "SUCCESS: Docker is already installed."
            docker --version
            exit 0
        fi

        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [ "$ID" = "ubuntu" ] || [ "$ID" = "debian" ]; then
                echo "Installing Docker Engine for $PRETTY_NAME..."

                echo "[1/6] Removing conflicting packages..."
                sudo apt-get remove -y docker docker-engine docker.io containerd runc || true

                echo "[2/6] Installing prerequisites..."
                sudo apt-get update
                sudo apt-get install -y ca-certificates curl gnupg lsb-release

                echo "[3/6] Adding Docker's official GPG key..."
                sudo install -m 0755 -d /etc/apt/keyrings
                sudo curl -fsSL https://download.docker.com/linux/$ID/gpg -o /etc/apt/keyrings/docker.asc
                sudo chmod a+r /etc/apt/keyrings/docker.asc

                echo "[4/6] Adding Docker repository..."
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$ID $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

                echo "[5/6] Installing Docker Engine and plugins..."
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

                echo "[6/6] Configuring rootless Docker access..."
                sudo usermod -aG docker $USER

                echo "================================================================================"
                echo "SUCCESS: Docker installation complete."
                echo "CRITICAL ACTION REQUIRED: You must log out of this SSH session and log back in"
                echo "to apply the 'docker' group permissions to the user '$USER'."
                echo "================================================================================"
            else
                echo "WARNING: Automatic installation is only supported for Ubuntu/Debian."
                echo "Please install Docker manually using the official convenience script:"
                echo "curl -fsSL https://get.docker.com | sh"
                exit 1
            fi
        else
            echo "FATAL: Cannot determine Linux distribution."
            exit 1
        fi
        ;;
    Darwin*)
        if command -v docker >/dev/null 2>&1; then
            echo "SUCCESS: Docker (or equivalent) is already installed."
            docker --version
            exit 0
        fi

        echo "Installing OrbStack for macOS..."
        if command -v brew >/dev/null 2>&1; then
            brew install --cask orbstack
            echo "SUCCESS: OrbStack installed. Please open the OrbStack app to initialize the Docker daemon."
        else
            echo "FATAL: Homebrew not found. Please install OrbStack manually from https://orbstack.dev"
            exit 1
        fi
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo "FATAL: Windows detected. Please install Docker Desktop manually:"
        echo "https://docs.docker.com/desktop/install/windows/"
        echo "Alternatively, inside a WSL2 Ubuntu instance, run this script again."
        exit 1
        ;;
    *)
        echo "FATAL: Unknown operating system: ${OS}"
        exit 1
        ;;
esac
