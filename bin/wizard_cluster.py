#!/usr/bin/env python3
import os
import json
import socket
import subprocess
import sys

def get_required_ssh_key():
    """
    Ensures the strict use of the MetaClaw deployment key for remote nodes.
    """
    home = os.path.expanduser("~")
    metaesque_key = os.path.join(home, ".ssh", "id_ed25519_metaesque")

    if not os.path.exists(metaesque_key):
        print(f"FATAL: Required SSH key not found at {metaesque_key}")
        sys.exit(1)

    return metaesque_key

def main():
    print("==================================================")
    print(" MetaClaw Distributed Wizard Bootstrapper")
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

        print(f"\n[Wizard] Provisioning node: {hostname} ({'Local' if is_local else 'Remote'})")
        print("-" * 60)

        if is_local:
            try:
                # Run the wizard-batch command natively on the orchestrating host
                subprocess.run(["make", "wizard-batch"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"FATAL: Local wizard-batch failed on {hostname}: {e}")
                sys.exit(1)
        else:
            ip = node.get("hardware", {}).get("ip_address")
            ssh_user = node.get("ssh_user", os.getlogin())

            # Using native ssh with pseudo-tty (-t) allows interactive streaming
            # of progress bars (like ollama pull) directly to the local terminal
            ssh_cmd = [
                "ssh", "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "-t",
                f"{ssh_user}@{ip}",
                "cd ~/repo && make wizard-batch"
            ]

            try:
                res = subprocess.run(ssh_cmd)
                if res.returncode != 0:
                    print(f"FATAL: Remote wizard-batch failed on {hostname} with exit code {res.returncode}")
                    sys.exit(1)
            except Exception as e:
                print(f"FATAL: Remote wizard-batch failed on {hostname}: {e}")
                sys.exit(1)

    print("\n==================================================")
    print(" SUCCESS: Cluster-wide wizard-batch complete.")
    print("==================================================")

if __name__ == "__main__":
    main()
