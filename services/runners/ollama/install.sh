#!/usr/bin/env bash
set -e

echo "Downloading Ollama Linux AMD64 binary..."
mkdir -p bin
curl -L https://ollama.com/download/ollama-linux-amd64 -o bin/ollama
chmod +x bin/ollama

echo "SUCCESS: Ollama installed to ./bin/ollama"
