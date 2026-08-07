#!/usr/bin/env python3
import os
import json
import socket
import subprocess
import sys

def get_ssh_key():
    home = os.path.expanduser("~")
    key = os.path.join(home, ".ssh", "id_ed25519_metaesque")
    if os.path.exists(key): return key
    return None

def main():
    profile_path = "profile.json"
    if not os.path.exists(profile_path):
        print("FATAL: profile.json not found. Run 'make setup' first.")
        sys.exit(1)

    with open(profile_path, "r") as f:
        profile = json.load(f)

    local_host = socket.gethostname()
    ssh_key = get_ssh_key()

    # Resolve the source-of-truth config directory
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_dir = os.environ.get('METACLAW_CONFIG')
    if not config_dir:
        config_dir = os.path.abspath(os.path.join(repo_root, '..', 'config'))

    hardware_dir = os.path.join(config_dir, 'data', 'hardware')

    print(f"Synchronizing remote hardware state back to: {hardware_dir}")
    os.makedirs(hardware_dir, exist_ok=True)

    for node in profile.get("nodes", []):
        hostname = node.get("hostname")
        ip = node.get("hardware", {}).get("ip_address")
        user = node.get("ssh_user", os.getlogin())

        if hostname == local_host or not ip or ip == "127.0.0.1":
            continue

        print(f"\n[Fetch State] Pulling hardware configurations from {hostname} ({ip})...")

        ssh_rsync_opts = "ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR"
        if ssh_key:
            ssh_rsync_opts += f" -i {ssh_key}"

        # Sync back the hardware directory without --delete to ensure we merge the node's JSON
        # into the master branch without overwriting data from other nodes.
        remote_hardware_dir = "~/config/data/hardware/"

        cmd = [
            "rsync", "-avz", "--info=progress2",
            "-e", ssh_rsync_opts,
            f"{user}@{ip}:{remote_hardware_dir}",
            f"{hardware_dir}/"
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  -> FAILED: Could not fetch from {hostname}. Error: {e}")

    print("\nSUCCESS: Hardware state synchronized to local config drop-zone.")

if __name__ == "__main__":
    main()
