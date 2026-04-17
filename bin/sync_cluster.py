import json
import os
import subprocess
import argparse
import socket

def _get_ip_address():
  """Retrieves the primary LAN IP address or Tailscale IP."""
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
  except Exception:
    return "127.0.0.1"

def main():
  parser = argparse.ArgumentParser(description="Synchronize profile.json across the MetaClaw cluster via rsync.")
  parser.add_argument('--dry-run', action='store_true', help="Print the rsync commands without executing them.")
  args = parser.parse_args()

  profile_path = "profile.json"
  if not os.path.exists(profile_path):
    print("[Cluster Sync] ERROR: profile.json not found. Run 'python bin/sysprofile.py' to generate one.")
    return

  with open(profile_path, 'r') as f:
    try:
      profile = json.load(f)
    except json.JSONDecodeError:
      print("[Cluster Sync] ERROR: profile.json is corrupted.")
      return

  local_ip = _get_ip_address()
  local_hostname = socket.gethostname()

  # Determine the absolute path of the framework root so we can sync to the same path on remote hosts.
  # Assuming uniform directory structures across cluster nodes.
  repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

  target_nodes = []
  for node in profile.get("nodes", []):
    node_ip = node.get("hardware", {}).get("ip_address")
    node_hostname = node.get("hostname")

    # Do not sync to ourselves
    if node_ip and node_ip != "127.0.0.1" and node_ip != local_ip and node_hostname != local_hostname:
      target_nodes.append(node_ip)

  if not target_nodes:
    print("[Cluster Sync] No remote nodes found in profile.json. Nothing to sync.")
    return

  user = os.environ.get("USER")

  print(f"[Cluster Sync] Initiating rsync push from Master Node ({local_hostname})...")

  for ip in set(target_nodes):
    # rsync -avz profile.json user@ip:/path/to/repo/
    target_dest = f"{user}@{ip}:{repo_root}/"
    cmd = ["rsync", "-avz", profile_path, target_dest]

    if args.dry_run:
      print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
    else:
      print(f"  -> Syncing to {ip}...")
      try:
        subprocess.run(cmd, check=True)
        print(f"  -> SUCCESS: Synced to {ip}")
      except subprocess.CalledProcessError as e:
        print(f"  -> FAILED: Could not sync to {ip}. Ensure SSH keys are configured. Error: {e}")

  print("[Cluster Sync] Complete. Remember to run 'make apply' on the remote nodes to enact the state change.")

if __name__ == "__main__":
  main()
