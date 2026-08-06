#!/usr/bin/env python3
import os
import json
import socket
import subprocess
import sys

def get_ssh_key():
    """
    Checks for the explicit MetaClaw deployment key.
    Falls back to None so the native ssh agent or ~/.ssh/config can take over.
    """
    home = os.path.expanduser("~")
    key = os.path.join(home, ".ssh", "id_ed25519_metaesque")
    if os.path.exists(key):
        return key
    return None

def run_cmd(cmd, shell=False):
    if isinstance(cmd, list):
        print(f"  > {' '.join(cmd)}")
    else:
        print(f"  > {cmd}")

    res = subprocess.run(cmd, shell=shell)

    if res.returncode != 0:
        print(f"\n[!] FATAL ERROR: Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    return res

def main():
    print("==================================================")
    print(" MetaClaw Distributed Pull & Sync")
    print("==================================================")

    profile_path = "profile.json"
    if not os.path.exists(profile_path):
        print("FATAL: profile.json not found. Run 'make setup' first.")
        sys.exit(1)

    with open(profile_path, "r") as f:
        profile = json.load(f)

    local_host = socket.gethostname()
    ssh_key = get_ssh_key()
    home = os.path.expanduser("~")

    # Command to fetch and hard reset to override any localized modifications
    git_cmd = "git fetch origin && BRANCH=$(git rev-parse --abbrev-ref HEAD) && git reset --hard origin/$BRANCH"

    for node in profile.get("nodes", []):
        hostname = node.get("hostname")
        ip = node.get("hardware", {}).get("ip_address")
        user = node.get("ssh_user", os.getlogin())

        is_local = (hostname == local_host)

        print(f"\n[Pull Sync] Node: {hostname} ({ip})")
        print("-" * 60)

        if is_local:
            repo_path = os.path.join(home, "repo")
            if os.path.exists(os.path.join(repo_path, ".git")):
                print(f"  -> Synchronizing local {repo_path}...")
                run_cmd(f"cd {repo_path} && {git_cmd}", shell=True)

            workspace_path = os.path.join(home, "workspace")
            if os.path.exists(os.path.join(workspace_path, ".git")):
                print(f"  -> Synchronizing local {workspace_path}...")
                run_cmd(f"cd {workspace_path} && {git_cmd}", shell=True)
        else:
            ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "LogLevel=ERROR"]
            if ssh_key:
                ssh_base.extend(["-i", ssh_key])
            ssh_base.append(f"{user}@{ip}")

            print("  -> Synchronizing remote ~/repo (if exists)...")
            repo_script = f"if [ -d ~/repo/.git ]; then cd ~/repo && {git_cmd}; else echo '     (No .git repository found at ~/repo. Skipping.)'; fi"
            run_cmd(ssh_base + [repo_script])

            print("  -> Synchronizing remote ~/workspace (if exists)...")
            workspace_script = f"if [ -d ~/workspace/.git ]; then cd ~/workspace && {git_cmd}; else echo '     (No .git repository found at ~/workspace. Skipping.)'; fi"
            run_cmd(ssh_base + [workspace_script])

            local_config = os.path.join(home, "config")
            if os.path.exists(local_config):
                print("  -> Rsyncing local ~/config to remote ~/config...")
                ssh_rsync_opts = "ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR"
                if ssh_key:
                    ssh_rsync_opts += f" -i {ssh_key}"

                rsync_cmd = [
                    "rsync", "-az", "--delete", "--info=progress2",
                    "-e", ssh_rsync_opts,
                    f"{local_config}/",
                    f"{user}@{ip}:~/config/"
                ]
                run_cmd(rsync_cmd)

if __name__ == "__main__":
    main()
