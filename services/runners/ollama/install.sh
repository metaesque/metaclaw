#!/usr/bin/env bash
set -e

if ! command -v ollama >/dev/null 2>&1; then
    echo "Installing Ollama system-wide..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

mkdir -p bin
ln -sf $(which ollama) bin/ollama

# Prevent the systemd daemon from automatically starting and conflicting with MetaClaw's port management
if systemctl is-active --quiet ollama; then
    echo "Stopping background systemd Ollama service to allow MetaClaw orchestration..."
    sudo systemctl stop ollama || true
    sudo systemctl disable ollama || true
fi

echo "SUCCESS: Ollama linked to ./bin/ollama"
