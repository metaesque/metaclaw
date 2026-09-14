#!/bin/bash
# Disables AI-Dock's default Thread-Caching Malloc (tcmalloc) optimization
# by stripping it from the supervisor script before boot.
# tcmalloc severely clashes with the AMD ROCm memory allocator on APUs.
sed -i 's/LD_PRELOAD=libtcmalloc.so //g' /opt/ai-dock/bin/supervisor-comfyui.sh
