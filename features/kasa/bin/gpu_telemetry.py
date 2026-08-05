#!/usr/bin/env python3
"""
Purpose: Gather GPU utilization, thermals, and VRAM data via Linux SysFS or nvidia-smi.
Outputs telemetry in Influx Line Protocol format.
"""

import subprocess
import os
import socket
import sys
import glob

def get_host():
    return os.environ.get("HOST_IDENTIFIER", socket.gethostname())

def poll_nvidia(host):
    try:
        # Check if command exists gracefully
        import shutil
        if not shutil.which("nvidia-smi"):
            # NVIDIA sysfs is locked down; if CLI fails, silently return.
            return

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 5:
                idx, util, temp, mem_used, mem_total = parts
                print(
                    f"gpu_telemetry,host={host},gpu_id=nvidia_{idx} "
                    f"utilization={util},temp_c={temp},vram_used_mb={mem_used},vram_total_mb={mem_total}"
                )
    except Exception as e:
        print(f"NVIDIA SMI parsing error: {e}", file=sys.stderr)

def poll_amd_sysfs(host):
    """
    Hardware-agnostic AMD telemetry extraction. Bypasses rocm-smi entirely
    by reading directly from the Linux kernel's DRM SysFS endpoint.
    Perfect for containerized environments where /sys is mounted to /hostfs/sys.
    """
    try:
        # Find all AMD DRM cards natively mapped by the host kernel
        cards = glob.glob("/hostfs/sys/class/drm/card*")

        # Fallback if testing locally outside the Telegraf container
        if not cards:
            cards = glob.glob("/sys/class/drm/card*")

        for card in cards:
            # Only process cards that expose a gpu_busy_percent file
            busy_file = os.path.join(card, "device", "gpu_busy_percent")
            if not os.path.exists(busy_file):
                continue

            idx = os.path.basename(card).replace("card", "")

            # 1. Utilization
            try:
                with open(busy_file, "r") as f:
                    util = float(f.read().strip())
            except Exception:
                util = 0.0

            # 2. Temperature
            temp = 0.0
            hwmon_dirs = glob.glob(os.path.join(card, "device", "hwmon", "hwmon*"))
            if hwmon_dirs:
                temp1_input = os.path.join(hwmon_dirs[0], "temp1_input")
                if os.path.exists(temp1_input):
                    try:
                        with open(temp1_input, "r") as f:
                            # Sysfs outputs millidegrees Celsius
                            temp = float(f.read().strip()) / 1000.0
                    except Exception:
                        pass

            # 3. VRAM
            vram_used_mb = 0.0
            vram_total_mb = 0.0
            mem_used_file = os.path.join(card, "device", "mem_info_vram_used")
            mem_total_file = os.path.join(card, "device", "mem_info_vram_total")

            try:
                if os.path.exists(mem_used_file):
                    with open(mem_used_file, "r") as f:
                        # Sysfs outputs bytes
                        vram_used_mb = float(f.read().strip()) / (1024 * 1024)
                if os.path.exists(mem_total_file):
                    with open(mem_total_file, "r") as f:
                        vram_total_mb = float(f.read().strip()) / (1024 * 1024)
            except Exception:
                pass

            print(
                f"gpu_telemetry,host={host},gpu_id=amd_{idx} "
                f"utilization={util},temp_c={temp},vram_used_mb={vram_used_mb:.1f},vram_total_mb={vram_total_mb:.1f}"
            )
    except Exception as e:
        print(f"AMD SysFS parsing error: {e}", file=sys.stderr)

if __name__ == "__main__":
    host = get_host()
    poll_nvidia(host)
    poll_amd_sysfs(host)

