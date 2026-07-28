#!/bin/bash
set -e

# Load orchestrator variables natively
if [ -f ../../../.env ]; then
    source ../../../.env
fi
if [ -f .env ]; then
    source .env
fi

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    OLLAMA_ARCH="amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    OLLAMA_ARCH="arm64"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

mkdir -p ./bin
cd ./bin

if [ -z "$OLLAMA_VERSION" ]; then
    echo "Fetching latest Ollama release version from GitHub API..."
    LATEST_RELEASE=$(curl -s https://api.github.com/repos/ollama/ollama/releases/latest | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')
    if [ -z "$LATEST_RELEASE" ]; then
        echo "Failed to fetch latest Ollama version. Network error?"
        exit 1
    fi
    OLLAMA_VERSION=$LATEST_RELEASE
fi

# Do not re-download if the binary already exists and is the correct version
if [ -x "ollama" ]; then
    CURRENT_VERSION=$(./ollama --version 2>/dev/null | awk '{print $NF}' | sed 's/^v//')
    if [ "$CURRENT_VERSION" = "$OLLAMA_VERSION" ]; then
        echo "Ollama v$OLLAMA_VERSION is already installed in ./bin."

        # We parse the array using IFS to safely detect the target model without quoting issues
        IFS=' ' read -r -a models <<< "$OLLAMA_TARGET_MODELS"
        for model in "${models[@]}"; do
            if [[ "$model" == *"ingu627/llama4-scout-q4:109b"* ]]; then
                echo "Compute Node Detected. Model template patching has been removed in favor of native LiteLLM stop sequences."
                break
            fi
        done

        exit 0
    else
        echo "Updating Ollama from v$CURRENT_VERSION to v$OLLAMA_VERSION..."
    fi
else
    echo "Downloading Ollama v$OLLAMA_VERSION for $OLLAMA_ARCH..."
fi

# Try .tar.zst modern archive format first, fallback to legacy .tgz
mkdir -p tmp_extract
if curl -f -sSL -o ollama.archive "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${OLLAMA_ARCH}.tar.zst"; then
    tar xf ollama.archive -C tmp_extract
elif curl -f -sSL -o ollama.archive "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${OLLAMA_ARCH}.tgz"; then
    tar xzf ollama.archive -C tmp_extract
else
    echo "Failed to download Ollama v${OLLAMA_VERSION} binary. Neither .tar.zst nor .tgz were found."
    rm -rf tmp_extract
    exit 1
fi

# ==============================================================================
# ARCHITECTURAL DECISION: Hermetic Installation vs Global APT
# ==============================================================================
# MetaClaw uses a hermetic, localized installation rather than a global APT package.
# Ollama updates extremely frequently (often daily for new model compatibility).
# Relying on OS package managers introduces severe lag. By downloading the artifact
# directly into the repository namespace, we strictly pin the Ollama daemon version
# to the framework state and isolate it from OS changes.
#
# To prevent port binding collisions and PATH resolution nightmares, we aggressively
# destroy any rogue global Ollama installations running in the background.

if [ -f "/usr/local/bin/ollama" ]; then
    echo "WARNING: Global Ollama installation detected at /usr/local/bin/ollama."
    echo "Destroying global daemon to prevent port conflicts with hermetic MetaClaw deployment..."
    sudo rm -f /usr/local/bin/ollama
    sudo systemctl stop ollama 2>/dev/null || true
    sudo systemctl disable ollama 2>/dev/null || true
fi

# Safely extract the binary
if [ -f "tmp_extract/bin/ollama" ]; then
    mv tmp_extract/bin/ollama .
fi

# Safely extract runner libraries to services/runners/ollama/lib/ollama
# This replaces the destructive '../lib' command that wiped out metaclaw.py
mkdir -p ../lib
if [ -d "tmp_extract/lib/ollama" ]; then
    rm -rf ../lib/ollama
    mv tmp_extract/lib/ollama ../lib/
fi

rm -rf tmp_extract ollama.archive

chmod +x ollama
echo "Ollama v$OLLAMA_VERSION installation complete."

# Re-run IFS parsing for first-time installation detection logging
IFS=' ' read -r -a models <<< "$OLLAMA_TARGET_MODELS"
for model in "${models[@]}"; do
    if [[ "$model" == *"ingu627/llama4-scout-q4:109b"* ]]; then
        echo "Compute Node Detected. Model template patching has been removed in favor of native LiteLLM stop sequences."
        break
    fi
done
