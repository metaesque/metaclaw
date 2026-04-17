#!/bin/bash
# Captures the state of openclaw.json before and after the agent modifies it.
CONFIG_PATH="services/gateways/openclaw/config/openclaw.json"
BACKUP_PATH="services/gateways/openclaw/config/openclaw.json.bak"

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: $CONFIG_PATH not found. Is the gateway service running?"
    exit 1
fi

if [ "$1" == "save" ]; then
    cp "$CONFIG_PATH" "$BACKUP_PATH"
    echo "Saved baseline config to $BACKUP_PATH."
    echo "Now tell the OpenClaw agent to 'Do it for me' (Option 1) in the GUI."
elif [ "$1" == "diff" ]; then
    if [ ! -f "$BACKUP_PATH" ]; then
        echo "No backup found. Run './bin/compare_config.sh save' first."
        exit 1
    fi
    echo "--- Config Changes Made by Agent Provider ---"
    # Using git diff if available for cleaner output, fallback to standard diff
    if command -v git >/dev/null 2>&1; then
        git diff --no-index "$BACKUP_PATH" "$CONFIG_PATH" || true
    else
        diff -u "$BACKUP_PATH" "$CONFIG_PATH" || true
    fi
else
    echo "Usage: ./bin/compare_config.sh [save|diff]"
fi
