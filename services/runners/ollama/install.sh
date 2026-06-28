#!/usr/bin/env bash
set -e

echo "Downloading Ollama Linux AMD64 archive..."
mkdir -p bin
curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o bin/ollama.tgz

echo "Extracting binary..."
tar -C . -xzf bin/ollama.tgz
rm bin/ollama.tgz

echo "SUCCESS: Ollama installed to ./bin/ollama"
