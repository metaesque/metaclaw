#!/bin/bash

# ==============================================================================
# Purpose: Watchdog script to monitor Kasa Power Daemon database heartbeat.
# Submits an alert to a Google Chat webhook if data is stale.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
DB_FILE="${SCRIPT_DIR}/../data/metaclaw_power.db"

# 1. Load webhook secret
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: WEBHOOK_URL is not set in $ENV_FILE"
    exit 1
fi

# 2. Query the latest telemetry timestamp (returns Unix epoch seconds)
LAST_POLL=$(sqlite3 "$DB_FILE" "SELECT strftime('%s', MAX(timestamp)) FROM telemetry;" 2>/dev/null)

if [ -z "$LAST_POLL" ]; then
    LAST_POLL=0
fi

# 3. Calculate staleness
NOW=$(date +%s)
DIFF=$((NOW - LAST_POLL))

# 4. Alert if stale (120 seconds threshold)
if [ "$DIFF" -gt 120 ]; then
    MESSAGE="⚠️ *Kasa Power Daemon Alert* ⚠️\nHeartbeat failed. No telemetry recorded in the database for $DIFF seconds."
    PAYLOAD="{\"text\": \"$MESSAGE\"}"

    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$WEBHOOK_URL" > /dev/null
fi

