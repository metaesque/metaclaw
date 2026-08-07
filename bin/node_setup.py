#!/usr/bin/env python3
import os
import sys
import socket
import subprocess

from lib import metaclaw

def main():
    print("==================================================")
    print(" MetaClaw Node Initialization")
    print("==================================================")

    hostname = socket.gethostname()
    print(f"Initializing node: {hostname}")

    mc = metaclaw.Inst
    devices = mc.devices()

    my_device = None
    for uid, dev in devices.items():
        if hostname.lower() in [uid.lower(), dev.name.lower()]:
            my_device = dev
            break

    if not my_device:
        print(f"WARNING: Hostname '{hostname}' not found in hardware registry. Skipping node-specific setup.")
        sys.exit(0)

    print(f"Device profile matched: {my_device.uid} ({my_device.device_type})")

    if my_device.device_type == 'node':
        clawdisk_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'features', 'clawdisk', 'bin', 'clawdisk_setup.py'))
        if os.path.exists(clawdisk_script):
            print(f"Executing ClawDisk storage mesh for {my_device.uid}...")
            subprocess.run([sys.executable, clawdisk_script, my_device.uid], check=True)
            print("ClawDisk setup verified.")
        else:
            print("ClawDisk feature not found. Skipping storage mesh setup.")

if __name__ == "__main__":
    main()
