#!/usr/bin/env python3
import sys
import os
import json
import socket
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python cluster_exec.py <make_target>")
        sys.exit(1)

    target = sys.argv[1]
    profile_path = "profile.json"

    if not os.path.exists(profile_path):
        print("FATAL: No profile.json found. Run 'make setup' first.")
        sys.exit(1)

    with open(profile_path, 'r') as f:
        profile = json.load(f)

    local_host = socket.gethostname()
    ssh_key = os.path.expanduser("~/.ssh/id_ed25519_metaesque")

    for node in profile.get("nodes", []):
        hostname = node.get("hostname")
        ip = node.get("hardware", {}).get("ip_address")
        user = node.get("ssh_user", os.getlogin())

        print(f"\n[Cluster Exec] Executing 'make {target}' on {hostname} ({ip})...")
        print("-" * 60)

        if hostname == local_host:
            subprocess.run(["make", target])
        else:
            cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "LogLevel=ERROR"]
            if os.path.exists(ssh_key):
                cmd.extend(["-i", ssh_key])
            cmd.extend([f"{user}@{ip}", f"cd ~/repo && make {target}"])
            subprocess.run(cmd)

if __name__ == "__main__":
    main()
