#!/usr/bin/env bash
# Verifies live OpenClaw configuration state directly from the running container.

if ! docker ps | grep -q openclaw-gateway; then
    echo "ERROR: openclaw-gateway container is not running."
    exit 1
fi

echo "================================================================================"
echo "Live OpenClaw Heartbeat Configuration"
echo "================================================================================"
echo -n "Interval: "
docker exec openclaw-gateway openclaw config get agents.defaults.heartbeat.every
echo -n "Target Model: "
docker exec openclaw-gateway openclaw config get agents.defaults.heartbeat.model

echo ""
echo "================================================================================"
echo "Live Global Router Configuration"
echo "================================================================================"
echo -n "Default Agent Model: "
docker exec openclaw-gateway openclaw config get agents.defaults.models.litellm/complex-model.alias || echo "Not strictly bound."
