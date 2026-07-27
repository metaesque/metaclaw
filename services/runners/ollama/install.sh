#!/usr/bin/env bash
set -e

mkdir -p bin

if [ ! -f "bin/ollama" ]; then
    echo "Downloading standalone Ollama Linux AMD64 binary..."
    curl -L https://ollama.com/download/ollama-linux-amd64 -o bin/ollama
    chmod +x bin/ollama
fi

# Prevent the systemd daemon from automatically starting and conflicting with MetaClaw's port management
# if it exists from a previous system-wide legacy installation.
if systemctl is-active --quiet ollama 2>/dev/null; then
    echo "Stopping background systemd Ollama service to allow MetaClaw orchestration..."
    sudo systemctl stop ollama || true
    sudo systemctl disable ollama || true
fi

echo "SUCCESS: Ollama binary is ready at ./bin/ollama"

