#!/bin/bash
set -e

if [ -z "$OLLAMA_VERSION" ]; then
  echo "FATAL: OLLAMA_VERSION is not set. Ensure .env is instantiated."
  exit 1
fi

mkdir -p ./bin
rm -f .updated

if [ -x "./bin/ollama" ]; then
  # Extract purely the semantic version number via regex to prevent parsing errors
  CURRENT_VERSION=$(./bin/ollama -v | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
  if [ "$CURRENT_VERSION" = "$OLLAMA_VERSION" ]; then
    echo "[Ollama Runner] Version $OLLAMA_VERSION is already installed."
    exit 0
  fi
  echo "Version mismatch or corrupted binary detected. Removing..."
  rm -f ./bin/ollama
fi

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; fi
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then ARCH="arm64"; fi

if [ "$OS" = "darwin" ]; then
  DOWNLOAD_URL="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/Ollama-darwin.zip"
  echo "Fetching Mac archive: $DOWNLOAD_URL..."
  curl -L "$DOWNLOAD_URL" -o ./bin/ollama.zip

  if [ $(wc -c <./bin/ollama.zip) -lt 1000 ]; then
    echo "FATAL: Download failed. Received error page instead of archive."
    rm ./bin/ollama.zip
    exit 1
  fi

  echo "Extracting binary from macOS app bundle..."
  unzip -q ./bin/ollama.zip -d ./bin/.tmp_mac
  mv ./bin/.tmp_mac/Ollama.app/Contents/Resources/ollama ./bin/ollama
  rm -rf ./bin/.tmp_mac ./bin/ollama.zip

elif [ "$OS" = "linux" ]; then
  DOWNLOAD_URL="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${ARCH}"
  echo "Fetching Linux binary: $DOWNLOAD_URL..."
  curl -L "$DOWNLOAD_URL" -o ./bin/ollama

  if [ $(wc -c <./bin/ollama) -lt 1000 ]; then
    echo "FATAL: Download failed. Received error page instead of binary."
    rm ./bin/ollama
    exit 1
  fi
else
  echo "FATAL: Unsupported OS architecture: $OS"
  exit 1
fi

chmod +x ./bin/ollama
echo "[Ollama Runner] Version $OLLAMA_VERSION successfully installed."
touch .updated
