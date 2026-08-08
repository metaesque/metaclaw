ARG TELEGRAF_VERSION=1.31
FROM telegraf:${TELEGRAF_VERSION}

# Switch to root to install dependencies
USER root

# Cache dependencies to speed up future builds
# ARCHITECTURAL SHIFT: Added smartmontools and nvme-cli to allow the
# native [[inputs.smart]] plugin to interrogate physical block devices via ioctls.
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv gcc python3-dev lm-sensors smartmontools nvme-cli && \
    rm -rf /var/lib/apt/lists/*

# Create and populate the virtual environment
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install python-kasa pyyaml && \
    chown -R telegraf:telegraf /opt/venv

# Telegraf base image natively handles the entrypoint, we simply provide the dependencies
