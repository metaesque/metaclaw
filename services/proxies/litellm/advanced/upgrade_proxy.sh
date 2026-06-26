#!/bin/bash

COMPOSE_FILE="../docker-compose.yml"
TEST_URL="http://localhost:4000/v1/chat/completions"
TARGET_VERSION="v1.35.0"

if [ -f ../.env ]; then
  set -a
  source ../.env
  set +a
else
  echo "FATAL: .env file not found."
  exit 1
fi

echo "========================================"
echo "LiteLLM Proxy Upgrade & Validation Suite"
echo "========================================"

echo "[1/4] Pulling defined image and recreating container..."
docker compose -f $COMPOSE_FILE pull
docker compose -f $COMPOSE_FILE up -d --force-recreate

echo "[2/4] Waiting for Uvicorn worker to open port 4000..."
max_attempts=15
attempt=1
while ! nc -z localhost 4000; do
  if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Container failed to expose port 4000 after 15 seconds."
    docker compose logs --tail=20 litellm-proxy
    exit 1
  fi
  sleep 1
  attempt=$((attempt + 1))
done
echo "Port 4000 is open."

echo "[3/4] Forcing semantic-router cold start to validate routing..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$TEST_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACTIVE_PROXY_KEY" \
  -d '{
    "model": "semantic-router",
    "messages": [{"role": "user", "content": "What is the capital of Australia?"}]
  }')

echo "[4/4] Evaluating HTTP Response..."
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "SUCCESS: Proxy returned HTTP 200. Routing is functional."
  exit 0
else
  echo "FATAL: Proxy returned HTTP $HTTP_STATUS."
  echo "ACTION REQUIRED: Check logs and rollback to previous tag."
  exit 1
fi
