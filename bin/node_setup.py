#!/usr/bin/env python3
import os
import sys
import socket

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

    if hasattr(my_device, 'mount_storage') and callable(getattr(my_device, 'mount_storage')):
        print(f"Executing storage mounts for {my_device.uid}...")
        my_device.mount_storage()
        print("Storage mounts verified.")
    else:
        print(f"Device type '{my_device.device_type}' does not support automated storage mounts.")

if __name__ == "__main__":
    main()
