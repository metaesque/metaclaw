#!/bin/bash
set -e

# Load orchestrator variables
if [ -f ../../../.env ]; then
    source ../../../.env
fi

if [ -f .env ]; then
    # Parse securely using grep. Avoids 'source .env' which crashes Bash (Error 127)
    # when processing unquoted space-separated Make loops like OLLAMA_TARGET_MODELS.
    export OLLAMA_TARGET_MODELS=$(grep "^OLLAMA_TARGET_MODELS=" .env | cut -d= -f2- | tr -d '"' | tr -d "'")
    export OLLAMA_PORT=$(grep "^OLLAMA_PORT=" .env | cut -d= -f2- | tr -d '"' | tr -d "'")
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

        # ==============================================================================
        # CUSTOM MODEL TEMPLATE INJECTION (FIX FOR LLAMA4-SCOUT JSON LEAK)
        # ==============================================================================
        # We must execute this even if Ollama is already downloaded.

        if echo "$OLLAMA_TARGET_MODELS" | grep -q "ingu627/llama4-scout-q4:109b"; then
            echo "Compute Node Detected. Patching broken llama4-scout tool template..."

            # Start a temporary daemon in the background to build the model if it's not running
            DAEMON_STARTED=0
            if ! curl -s http://127.0.0.1:${OLLAMA_PORT:-11434}/api/tags > /dev/null; then
                echo "Starting temporary Ollama daemon for model patching..."
                OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} OLLAMA_MODELS=${EXTERNAL_DRIVE_PATH:-/tmp}/ollama-models ./ollama serve > /dev/null 2>&1 &
                DAEMON_PID=$!
                DAEMON_STARTED=1
                sleep 5
            fi

            # Pull the base weights if they don't exist
            OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} ./ollama pull ingu627/llama4-scout-q4:109b || true

            # Create a fixed Modelfile that forces LiteLLM-compatible XML tool markers and strict stop tokens
            cat << 'EOF' > Modelfile.llama4-fixed
FROM ingu627/llama4-scout-q4:109b

PARAMETER stop "<|eot|>"
PARAMETER stop "<|header_start|>"
PARAMETER stop "<|header_end|>"
PARAMETER stop "</tool_call>"

TEMPLATE """{{- if .System }}<|header_start|>system<|header_end|>
{{ .System }}
{{- end }}
{{- if .Tools }}
You are an intelligent agent equipped with native function calling. To execute a function, you MUST wrap your JSON payload strictly inside <tool_call> tags.
Example: <tool_call>{"name": "get_weather", "arguments": {"location": "Paris"}}</tool_call>
Do NOT output conversational text alongside the tool call.
Available tools:
{{- range .Tools }}
- {{ .Function.Name }}: {{ .Function.Description }}
  Arguments Schema: {{ .Function.Parameters }}
{{- end }}
{{- end }}<|eot|>
{{- range .Messages }}
{{- if eq .Role "user" }}<|header_start|>user<|header_end|>
{{ .Content }}<|eot|>
{{- else if eq .Role "assistant" }}<|header_start|>assistant<|header_end|>
{{- if .ToolCalls }}
{{- range .ToolCalls }}<tool_call>{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}</tool_call>{{ end }}
{{- else }}{{ .Content }}<|eot|>
{{- end }}
{{- else if eq .Role "tool" }}<|header_start|>ipython<|header_end|>
{{ .Content }}<|eot|>
{{- end }}
{{- end }}<|header_start|>assistant<|header_end|>
"""
EOF

            echo "Building metaclaw-llama4-scout..."
            OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} ./ollama create metaclaw-llama4-scout -f Modelfile.llama4-fixed
            rm Modelfile.llama4-fixed

            if [ $DAEMON_STARTED -eq 1 ]; then
                echo "Stopping temporary daemon..."
                kill $DAEMON_PID 2>/dev/null || true
            fi
        fi

        exit 0
    else
        echo "Updating Ollama from v$CURRENT_VERSION to v$OLLAMA_VERSION..."
    fi
else
    echo "Downloading Ollama v$OLLAMA_VERSION for $OLLAMA_ARCH..."
fi

# Try .tar.zst modern archive format first, fallback to legacy .tgz
if curl -f -sSL -o ollama.archive "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${OLLAMA_ARCH}.tar.zst"; then
    tar xf ollama.archive
elif curl -f -sSL -o ollama.archive "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${OLLAMA_ARCH}.tgz"; then
    tar xzf ollama.archive
else
    echo "Failed to download Ollama v${OLLAMA_VERSION} binary. Neither .tar.zst nor .tgz were found."
    exit 1
fi

# Modern Ollama archives extract into 'bin/ollama' and 'lib/ollama/...'.
# Because we are in ./bin, tar creates nested directories. We must elevate them.
if [ -f "bin/ollama" ]; then
    mv bin/ollama ./ollama
elif [ -f "./bin/ollama" ]; then
    mv ./bin/ollama ./ollama
fi

if [ -d "lib" ]; then
    rm -rf ../lib
    mv lib ../
elif [ -d "./lib" ]; then
    rm -rf ../lib
    mv ./lib ../
fi

rm -rf bin ./bin ollama.archive

chmod +x ollama
echo "Ollama v$OLLAMA_VERSION installation complete."

# ==============================================================================
# CUSTOM MODEL TEMPLATE INJECTION (FIX FOR LLAMA4-SCOUT JSON LEAK)
# ==============================================================================
if echo "$OLLAMA_TARGET_MODELS" | grep -q "ingu627/llama4-scout-q4:109b"; then
    echo "Compute Node Detected. Patching broken llama4-scout tool template..."

    # Start a temporary daemon in the background to build the model if it's not running
    DAEMON_STARTED=0
    if ! curl -s http://127.0.0.1:${OLLAMA_PORT:-11434}/api/tags > /dev/null; then
        echo "Starting temporary Ollama daemon for model patching..."
        OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} OLLAMA_MODELS=${EXTERNAL_DRIVE_PATH:-/tmp}/ollama-models ./ollama serve > /dev/null 2>&1 &
        DAEMON_PID=$!
        DAEMON_STARTED=1
        sleep 5
    fi

    # Pull the base weights if they don't exist
    OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} ./ollama pull ingu627/llama4-scout-q4:109b || true

    # Create a fixed Modelfile that forces LiteLLM-compatible XML tool markers and strict stop tokens
    cat << 'EOF' > Modelfile.llama4-fixed
FROM ingu627/llama4-scout-q4:109b

PARAMETER stop "<|eot|>"
PARAMETER stop "<|header_start|>"
PARAMETER stop "<|header_end|>"
PARAMETER stop "</tool_call>"

TEMPLATE """{{- if .System }}<|header_start|>system<|header_end|>
{{ .System }}
{{- end }}
{{- if .Tools }}
You are an intelligent agent equipped with native function calling. To execute a function, you MUST wrap your JSON payload strictly inside <tool_call> tags.
Example: <tool_call>{"name": "get_weather", "arguments": {"location": "Paris"}}</tool_call>
Do NOT output conversational text alongside the tool call.
Available tools:
{{- range .Tools }}
- {{ .Function.Name }}: {{ .Function.Description }}
  Arguments Schema: {{ .Function.Parameters }}
{{- end }}
{{- end }}<|eot|>
{{- range .Messages }}
{{- if eq .Role "user" }}<|header_start|>user<|header_end|>
{{ .Content }}<|eot|>
{{- else if eq .Role "assistant" }}<|header_start|>assistant<|header_end|>
{{- if .ToolCalls }}
{{- range .ToolCalls }}<tool_call>{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}</tool_call>{{ end }}
{{- else }}{{ .Content }}<|eot|>
{{- end }}
{{- else if eq .Role "tool" }}<|header_start|>ipython<|header_end|>
{{ .Content }}<|eot|>
{{- end }}
{{- end }}<|header_start|>assistant<|header_end|>
"""
EOF

    echo "Building metaclaw-llama4-scout..."
    OLLAMA_HOST=127.0.0.1:${OLLAMA_PORT:-11434} ./ollama create metaclaw-llama4-scout -f Modelfile.llama4-fixed
    rm Modelfile.llama4-fixed

    if [ $DAEMON_STARTED -eq 1 ]; then
        echo "Stopping temporary daemon..."
        kill $DAEMON_PID 2>/dev/null || true
    fi
fi
