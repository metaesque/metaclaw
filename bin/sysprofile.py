import platform
import os
import subprocess
import shutil
import json
import argparse
import socket
import uuid
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import metaclaw

def _get_ip_address():
  """Retrieves the primary LAN IP address for cross-node communication."""
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
  except Exception:
    return "127.0.0.1"

def _run_cmd(cmd):
  try:
    result = subprocess.run(
      cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
      text=True, check=True
    )
    return result.stdout.strip()
  except (subprocess.CalledProcessError, FileNotFoundError):
    return None

def _get_mac_gpu():
  output = _run_cmd(['system_profiler', 'SPDisplaysDataType', '-json'])
  if not output:
    return "Unknown Mac GPU", 0
  try:
    data = json.loads(output)
    cards = data.get('SPDisplaysDataType', [])
    if cards:
      card = cards[0]
      name = card.get('sppci_model', 'Apple Silicon')
      return name, 0
  except json.JSONDecodeError:
    pass
  return "Unknown Mac GPU", 0

def _get_linux_gpu(ram_bytes=0):
  # Check NVIDIA
  nvidia = _run_cmd([
    'nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'
  ])
  if nvidia:
    parts = nvidia.split(',')
    name = parts[0].strip()
    vram_mb = int(parts[1].replace('MiB', '').strip())
    return name, vram_mb * 1024 * 1024

  # Check AMD APU (Strix Halo / Ryzen AI Max) first
  cpu_info = _run_cmd(['cat', '/proc/cpuinfo'])
  if cpu_info and 'Ryzen AI Max' in cpu_info:
    # Strix Halo allocates VRAM dynamically from system RAM.
    # We estimate 75% of total system RAM is addressable by the APU for inference.
    vram_mb = int((ram_bytes * 0.75) / (1024 * 1024))
    return "AMD Ryzen AI Max+ APU (Strix Halo)", vram_mb * 1024 * 1024

  # Check AMD ROCm
  rocm = _run_cmd(['rocm-smi', '--showproductname'])
  if rocm:
    lspci = _run_cmd(['lspci'])
    if lspci:
      for line in lspci.split('\n'):
        if 'VGA' in line and 'Advanced Micro Devices' in line:
          return "AMD Radeon GPU (ROCm)", 0

  return "No Discrete GPU Detected", 0

def platform_details():
  sys_os = platform.system()
  arch = platform.machine()
  cpu_cores = os.cpu_count() or 1

  try:
    ram_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
  except (AttributeError, ValueError):
    ram_bytes = 0

  total_storage, used_storage, free_storage = shutil.disk_usage('/')

  ukeys = ['system', 'node', 'release', 'version', 'machine']
  uname = dict(zip(ukeys + ['processor'], list(platform.uname())))
  os_uname = dict(zip(ukeys, list(os.uname())))
  for ukey in ukeys:
    pval = uname[ukey]
    oval = os_uname[ukey]
    if pval != oval:
      print(
        'WARNING: %-20 user-facing "%s" != "%s" kernel' % (ukey, pval, oval)
      )

  details = {
    "os": sys_os,
    "architecture": arch,
    "ip_address": _get_ip_address(),
    "cpu_cores": cpu_cores,
    "ram_bytes": ram_bytes,
    "ram_gb": round(ram_bytes / (1024**3), 2),
    "storage_total_gb": round(total_storage / (1024**3), 2),
    "storage_free_gb": round(free_storage / (1024**3), 2),
    "unified_memory": False,
    "gpu_name": "Unknown",
    "vram_gb": 0.0,
    "uname": uname,
    "os_uname": os_uname,
  }

  if sys_os == 'Darwin':
    details['gpu_name'], _ = _get_mac_gpu()
    if arch == 'arm64':
      details['unified_memory'] = True
      vram_bytes = int(ram_bytes * 0.7)
      details['vram_gb'] = round(vram_bytes / (1024**3), 2)

  elif sys_os == 'Linux':
    details['gpu_name'], vram_bytes = _get_linux_gpu(ram_bytes)
    if vram_bytes > 0:
      details['vram_gb'] = round(vram_bytes / (1024**3), 2)

  return details

def main():
  parser = argparse.ArgumentParser(
    description="Generate a MetaClaw hardware and provider profile."
  )
  parser.add_argument(
    '-t', '--tier', type=int, default=-1,
    help="The architectural tier (0-4) of the cluster this node joins/forms."
  )
  parser.add_argument(
    '-w', '--wan', type=str, default="",
    help="Require WAN access (y/n)."
  )
  parser.add_argument(
    '-o', '--order', type=str, default="",
    help="Priority order for provider selection (e.g. safety,cost,resources)"
  )
  args = parser.parse_args()

  tier = args.tier
  if tier == -1:
    border = "=" * 80
    print(border)
    print(" Meta<Claw> Cluster Profiler")
    print(border)
    print("Select the cluster architectural tier this machine represents/joins:")
    print("  [0] Tier 0: The Day 1 Minilith (Constrained dual-use laptop)")
    print("  [1] Tier 1: The Month 2 Monolith (Dedicated Mini-PC, all-in-one)")
    print("  [2] Compute Node (Advances cluster to Tier 2: Data Sovereignty)")
    print("  [3] Execution Node (Advances cluster to Tier 3: Sandbox Extraction)")
    print("  [4] Archive Node (Advances cluster to Tier 4: Archive Expansion)")
    default_tier = 0
    while True:
      try:
        choice = input("Enter tier [%s]: " % default_tier)
        if not choice:
          tier = default_tier
          break
        else:
          choice = int(choice)
          if 0 <= choice <= 4:
            tier = choice
            break
          else:
            print("Please enter a number between 0 and 4.")
      except ValueError:
        print("Invalid input. Please enter an integer.")

  wan_input = args.wan.lower()
  if wan_input not in ['y', 'n', 'yes', 'no']:
    print("\nDo you require remote WAN access to your cluster while traveling,")
    print("or the ability to receive external webhooks (e.g., Telegram bots)?")
    print("If you only plan to use OpenClaw on your home Wi-Fi, answer No.")
    while True:
      wan_choice = input("Require WAN access? [Y/n]: ").strip().lower()
      # Defaulting to 'yes' if empty string is provided
      if wan_choice in ['y', 'yes', '']:
        require_wan = True
        break
      elif wan_choice in ['n', 'no']:
        require_wan = False
        break
  else:
    require_wan = wan_input in ['y', 'yes']

  order_input = args.order
  valid_options = {'safety', 'cost', 'resources'}
  if not order_input:
    default_order = 'cost,safety,resources'
    print("\nPlease specify your priority order for provider selection.")
    print("Provide 'safety', 'cost', and 'resources' separated by commas in your preferred order.")
    print("Example: " + default_order)
    while True:
      o_choice = input("Enter priority order [%s]: " % default_order).strip().lower()
      if o_choice == "":
        order_input = default_order
        break
      parts = [p.strip() for p in o_choice.split(',')]
      if len(parts) == 3 and set(parts) == valid_options:
        order_input = ",".join(parts)
        break
      else:
        print("Invalid input. You must provide exactly 'safety', 'cost', and 'resources' separated by commas.")
  else:
    parts = [p.strip() for p in order_input.split(',')]
    if len(parts) != 3 or set(parts) != valid_options:
      print(f"FATAL: Invalid --order argument '{order_input}'. Must be a permutation of safety,cost,resources.")
      sys.exit(1)
    order_input = ",".join(parts)

  profile_path = "profile.json"
  if os.path.exists(profile_path):
    with open(profile_path, 'r') as f:
      profile = json.load(f)
  else:
    profile = {
      "cluster_id": f"metaclaw-cluster-{str(uuid.uuid4())[:8]}",
      "nodes": []
    }

  hw_details = platform_details()
  hostname = socket.gethostname()
  order_prefs = order_input.split(',')

  profile = metaclaw.Inst.updateCluster(
    profile, hostname, tier, hw_details, require_wan, order_prefs
  )

  # Override network to strictly treat Tailscale as a bare-metal lifeline
  # This prevents docker compose teardowns from severing SSH connections
  if require_wan:
    for node in profile.get("nodes", []):
      if "network" in node.get("providers", {}):
        node["providers"]["network"]["metal"] = True

  with open(profile_path, 'w') as f:
    json.dump(profile, f, indent=2)

  print(f"\n[Profile] Node '{hostname}' registered as Tier {tier}.")
  wan_str = 'Enabled (Lifeline Protected)' if require_wan else 'Disabled'
  print(f"[Profile] Network mesh (Tailscale) set to: {wan_str}")
  prefs_str = ' > '.join([p.capitalize() for p in order_prefs])
  print(f"[Profile] Priorities set to: {prefs_str}")
  print(
    "[Profile] Cluster state updated in profile.json.\n"
    "Run 'make apply' or 'make wizard' to enact changes."
  )

if __name__ == '__main__':
  main()
