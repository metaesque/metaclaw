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
    local_node_dir = os.path.join(hardware_dir, 'node')

    print(f"Synchronizing remote hardware state back to: {local_node_dir}")
    os.makedirs(local_node_dir, exist_ok=True)

    for node in profile.get("nodes", []):
        hostname = node.get("hostname")
        ip = node.get("hardware", {}).get("ip_address")
        user = node.get("ssh_user", os.getlogin())

        if hostname == local_host or not ip or ip == "127.0.0.1":
            continue

        print(f"\n[Pull Config] Pulling hardware configuration from {hostname} ({ip})...")

        ssh_rsync_opts = "ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR"
        if ssh_key:
            ssh_rsync_opts += f" -i {ssh_key}"

        # Sync ONLY the specific node JSON file to prevent overwriting other node configs
        remote_hardware_file = f"~/config/data/hardware/node/{hostname}.json"

        cmd = [
            "rsync", "-avz",
            "-e", ssh_rsync_opts,
            f"{user}@{ip}:{remote_hardware_file}",
            f"{local_node_dir}/"
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  -> FAILED: Could not fetch from {hostname}. Error: {e}")

    print("\nSUCCESS: Hardware state synchronized to local config drop-zone.")

if __name__ == "__main__":
    main()
