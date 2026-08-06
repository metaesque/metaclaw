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

def print_disk_status(ip, ssh_user, ssh_key, is_local):
    print("\n" + "=" * 60)
    print(" DEVICE STATUS (ACCESSIBLE DISKS)")
    print("=" * 60)
    # Fetch the header and filter out ephemeral/pseudo filesystems for clarity
    cmd = "df -Ph | head -n 1 && df -Ph | grep -vE '^Filesystem|tmpfs|devtmpfs|squashfs|overlay|loop|udev|map'"

    if is_local:
        subprocess.run(cmd, shell=True)
    else:
        ssh_cmd = [
            "ssh", "-i", ssh_key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            f"{ssh_user}@{ip}",
            cmd
        ]
        subprocess.run(ssh_cmd)
    print("")

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

        # Reversing the emphasis: Massive banner for the Node transition
        print("\n\n" + "#" * 80)
        print(f"# 🖥️  NODE: {hostname.upper()} ({'LOCAL' if is_local else 'REMOTE'})")
        print("#" * 80)

        # Show accessible disks
        ip = node.get("hardware", {}).get("ip_address")
        ssh_user = node.get("ssh_user", os.getlogin())

        print_disk_status(ip, ssh_user, ssh_key, is_local)

        # Show status of local services
        if is_local:
            subprocess.run(["make", "status-local"])
        else:
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
