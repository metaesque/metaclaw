#!/usr/bin/env python3
import os
import json
import socket
import subprocess
import sys

def get_required_ssh_key():
    home = os.path.expanduser("~")
    metaesque_key = os.path.join(home, ".ssh", "id_ed25519_metaesque")
    if not os.path.exists(metaesque_key):
        print(f"FATAL: Required SSH key not found at {metaesque_key}")
        sys.exit(1)
    return metaesque_key

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Status")
    print("==================================================")

    if not os.path.exists("profile.json"):
        print("FATAL: profile.json not found. Run 'make setup' first.")
        sys.exit(1)

    with open("profile.json", "r") as f:
        profile = json.load(f)

    local_host = socket.gethostname()
    ssh_key = get_required_ssh_key()

    for node in profile.get("nodes", []):
        hostname = node.get("hostname")
        is_local = (hostname == local_host)

        print(f"\n[Status] Node: {hostname} ({'Local' if is_local else 'Remote'})")
        print("-" * 60)

        if is_local:
            subprocess.run(["make", "status-local"])
        else:
            ip = node.get("hardware", {}).get("ip_address")
            ssh_user = node.get("ssh_user", os.getlogin())

            ssh_cmd = [
                "ssh", "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                f"{ssh_user}@{ip}",
                "cd ~/repo && make status-local"
            ]
            subprocess.run(ssh_cmd)

if __name__ == "__main__":
    main()
