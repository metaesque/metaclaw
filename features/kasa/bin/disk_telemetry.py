#!/usr/bin/env python3
"""
Purpose: Gather local SSD usage metrics for Grafana.
Outputs telemetry in Influx Line Protocol format.
"""

import os
import sys
import socket
import subprocess
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "lib"))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from devices import get_all_devices

def get_attached_uuids():
    """
    Executes lsblk to find the UUIDs of all block devices physically attached to this host.
    Bypasses mount namespace issues by querying block devices directly.
    """
    attached = set()
    try:
        res = subprocess.run(['lsblk', '-J', '-o', 'NAME,UUID'], capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            def extract(blocks):
                for b in blocks:
                    if b.get('uuid'):
                        attached.add(b['uuid'].lower())
                    if 'children' in b:
                        extract(b['children'])
            extract(data.get('blockdevices', []))
    except Exception:
        pass
    return attached

def main():
    devices = get_all_devices()
    current_hostname = socket.gethostname().lower()
    attached_uuids = get_attached_uuids()

    for uid, dev in devices.items():
        if dev.device_type in ['node', 'compute_node']:
            # Only the node itself should report its own root storage
            if current_hostname in uid.lower() or current_hostname in dev.name.lower():
                try:
                    # Statically map to the host's root filesystem mount
                    st = os.statvfs('/hostfs')
                    total = st.f_blocks * st.f_frsize
                    free = st.f_bavail * st.f_frsize
                    used = total - free
                    if total > 0:
                        percent = (used / total) * 100.0
                        print(f"disk_telemetry,device={uid}_root used_bytes={used}i,total_bytes={total}i,used_percent={percent:.2f}")
                except Exception:
                    pass

        elif dev.device_type == 'ssd':
            # For external SSDs, verify they are physically attached to THIS node
            for m in dev.data.get('mounts', []):
                uuid = m.get('uuid', '').lower()
                mp = m.get('mountpoint')

                if not uuid or not mp:
                    continue

                # If the drive's UUID isn't in lsblk, it's plugged into a different cluster node
                if uuid not in attached_uuids:
                    continue

                host_mp = f"/hostfs{mp}"
                if not os.path.exists(host_mp):
                    host_mp = mp

                try:
                    st = os.statvfs(host_mp)
                    total = st.f_blocks * st.f_frsize
                    free = st.f_bavail * st.f_frsize
                    used = total - free
                    if total > 0:
                        percent = (used / total) * 100.0
                        print(f"disk_telemetry,device={uid} used_bytes={used}i,total_bytes={total}i,used_percent={percent:.2f}")
                except Exception:
                    pass

if __name__ == "__main__":
    main()
