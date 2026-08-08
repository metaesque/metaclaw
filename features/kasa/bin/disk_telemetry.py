#!/usr/bin/env python3
"""
Purpose: Gather local SSD usage metrics for Grafana.
Outputs telemetry in Influx Line Protocol format.
"""

import os
import sys
import socket

script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "lib"))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from devices import get_all_devices

def get_local_mounts():
    mounts = set()
    # Check both the hostfs mount and the standard container proc
    # to guarantee visibility across different namespace isolation topologies
    for proc_path in ['/hostfs/proc/mounts', '/proc/mounts']:
        if os.path.exists(proc_path):
            try:
                with open(proc_path, 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            dev_path = parts[0]
                            mp = parts[1]
                            # Only track real local block devices, skip nfs, overlay, etc.
                            if dev_path.startswith('/dev/'):
                                mounts.add(mp)
            except Exception as e:
                pass
    return mounts

def main():
    devices = get_all_devices()
    local_mounts = get_local_mounts()
    current_hostname = socket.gethostname().lower()

    for uid, dev in devices.items():
        # Dynamically trigger lsblk to discover mounts if they aren't statically defined
        if dev.device_type in ['node', 'compute_node']:
            if current_hostname in uid.lower() or current_hostname in dev.name.lower():
                try:
                    dev.update_data()
                except Exception:
                    pass

        for m in dev.data.get('mounts', []):
            mp = m.get('mountpoint')
            if not mp:
                continue

            # Ensure it is a local mount (to avoid duplicate NFS reporting via ClawDisk)
            if mp not in local_mounts:
                continue

            if mp == '/':
                host_mp = '/hostfs'
                dev_name = f"{uid}_root"
            else:
                host_mp = f"/hostfs{mp}"
                # Fallback if hostfs wasn't mounted cleanly
                if not os.path.exists(host_mp):
                    host_mp = mp
                dev_name = uid if dev.device_type == 'ssd' else f"{uid}_{os.path.basename(mp)}"

            try:
                st = os.statvfs(host_mp)
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                used = total - free
                if total > 0:
                    percent = (used / total) * 100.0
                    print(f"disk_telemetry,device={dev_name} used_bytes={used}i,total_bytes={total}i,used_percent={percent:.2f}")
            except Exception as e:
                pass

if __name__ == "__main__":
    main()
