import platform
import os
import subprocess
import shutil
import json
import argparse
import socket
import uuid
import sys
import re

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
    # Strix Halo allocates up to 96GB (roughly 3x the standard OS visibility)
    vram_bytes = int(ram_bytes * 3.0)
    return "AMD Ryzen AI Max+ APU (Strix Halo)", vram_bytes

  # Check AMD ROCm
  rocm = _run_cmd(['rocm-smi', '--showproductname'])
  if rocm:
    lspci = _run_cmd(['lspci'])
    if lspci:
      for line in lspci.split('\n'):
        if 'VGA' in line and 'Advanced Micro Devices' in line:
          return "AMD Radeon GPU (ROCm)", 0

  return "No Discrete GPU Detected", 0

def _is_tailscale_running():
  """Checks if the Tailscale daemon is currently running on the host OS."""
  try:
    result = subprocess.run(['tailscale', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0
  except FileNotFoundError:
    return False

def _get_hardware_ram_linux():
  """
  Extracts total physical hardware RAM via lshw to completely bypass the
  need for sudo/dmidecode passwords over SSH, preventing silent failures.
  """
  try:
    # lshw -class memory often has permissions to read basic capacity sizes
    # out of sysfs even without sudo, avoiding password prompts.
    # Alternatively, we just extract from /proc/meminfo if running inside a container.
    lshw_out = _run_cmd(['lshw', '-class', 'memory', '-json'])
    if lshw_out:
      data = json.loads(lshw_out)
      total_bytes = 0
      # lshw can return a list or a dict depending on the hardware layout
      nodes = data if isinstance(data, list) else [data]
      for node in nodes:
        if node.get('id') == 'memory':
          size = node.get('size', 0)
          if size:
            return int(size) / (1024**3)
  except Exception:
    pass

  return None

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

  details = {
    "os": sys_os,
    "architecture": arch,
    "ip_address": _get_ip_address(),
    "cpu_cores": cpu_cores,
    "ram_bytes": ram_bytes,
    "ram_gb": round(ram_bytes / (1024**3), 2),
    "ram_hardware_gb": round(ram_bytes / (1024**3), 2),
    "storage_total_gb": round(total_storage / (1024**3), 2),
    "storage_free_gb": round(free_storage / (1024**3), 2),
    "unified_memory": False,
    "gpu_detected": "No Discrete GPU Detected",
    "vram_gb": 0.0,
    "tailscale_active": _is_tailscale_running(),
    "uname": uname,
    "os_uname": os_uname,
  }

  if sys_os == 'Darwin':
    details['gpu_detected'], _ = _get_mac_gpu()
    if arch == 'arm64':
      details['unified_memory'] = True
      vram_bytes = int(ram_bytes * 0.7)
      details['vram_gb'] = round(vram_bytes / (1024**3), 2)

  elif sys_os == 'Linux':
    details['gpu_detected'], vram_bytes = _get_linux_gpu(ram_bytes)
    hw_ram = _get_hardware_ram_linux()

    if hw_ram:
      details['ram_hardware_gb'] = float(hw_ram)
    elif cpu_cores == 32 and 28.0 <= details['ram_gb'] <= 32.0:
      # Bulletproof heuristic for EVO-X2 (Strix Halo)
      # 32 CPU cores (16c/32t) + 31GB OS RAM implies 128GB physical with 96GB UMA reserved.
      details['ram_hardware_gb'] = 128.0
      details['gpu_detected'] = "AMD Ryzen AI Max+ APU (Strix Halo)"
      details['unified_memory'] = True
      details['vram_gb'] = 96.0
    elif cpu_cores == 16 and 26.0 <= details['ram_gb'] <= 29.0:
      # Heuristic for K8 Plus (8c/16t) with ~28GB OS RAM implies 32GB physical.
      details['ram_hardware_gb'] = 32.0

    if vram_bytes > 0 and not details['unified_memory']:
      details['vram_gb'] = round(vram_bytes / (1024**3), 2)

  return details

def main():
  parser = argparse.ArgumentParser(description="Generate a MetaClaw hardware and provider profile.")
  parser.add_argument('-t', '--tier', type=str, default="", help="The architectural tier (0, 1, 2, 3A, 3E, 4) of the cluster.")
  parser.add_argument('-p', '--planes', type=str, default="", help="Comma-separated planes this host represents.")
  parser.add_argument('-w', '--wan', type=str, default="", help="Require WAN access (y/n).")
  parser.add_argument('-hl', '--headless', type=str, default="", help="Is this node a headless server? (y/n)")
  parser.add_argument('-o', '--order', type=str, default="", help="Priority order for provider selection.")
  args = parser.parse_args()

  tier = args.tier
  if not tier:
    border = "=" * 80
    print(border)
    print(" Meta<Claw> Cluster Profiler")
    print(border)
    print("What tier is this host in?")
    print("  [0]  Tier 0: The Day 1 Minilith (Constrained dual-use laptop)")
    print("  [1]  Tier 1: The Month 2 Monolith (Dedicated Mini-PC, all-in-one)")
    print("  [2]  Tier 2: Data Sovereignty (Adds Compute Node)")
    print("  [3A] Tier 3A: Archive Extraction (Adds Archive Node)")
    print("  [3E] Tier 3E: Sandbox Extraction (Adds Execution Node)")
    print("  [4]  Tier 4: The Distributed Farm (4 Nodes)")
    default_tier = "0"
    while True:
      choice = input("Enter tier [%s]: " % default_tier).strip().upper()
      if not choice:
        tier = default_tier
        break
      elif choice in ['0', '1', '2', '3A', '3E', '4']:
        tier = choice
        break
      else:
        print("Please enter a valid tier (0, 1, 2, 3A, 3E, 4).")
  else:
    tier = tier.strip().upper()

  planes_input = args.planes
  if not planes_input:
    if tier in ["0", "1"]:
      planes_input = "control,compute,execution,archive"
    elif tier == "2":
      print("\nWhat role does this node play in your Tier 2 cluster?")
      print("  [1] Compute node (provides access to large LLMs)")
      print("  [2] Control node without runner (control + execution + archive)")
      print("  [3] Control node with all planes")
      while True:
        choice = input("Enter choice [1]: ").strip()
        if not choice or choice == '1':
          planes_input = "compute"
          break
        elif choice == '2':
          planes_input = "control,execution,archive"
          break
        elif choice == '3':
          planes_input = "control,compute,execution,archive"
          break
        else:
          print("Invalid choice. Enter 1, 2, or 3.")
    elif tier == "3A":
      print("\nWhat role does this node play in your Tier 3A cluster?")
      print("  [1] Compute node (provides access to large LLMs)")
      print("  [2] Archive node (vector databases and observability)")
      print("  [3] Control node without runner (control + execution)")
      print("  [4] Control node with runner (control + execution + compute)")
      while True:
        choice = input("Enter choice [1]: ").strip()
        if not choice or choice == '1':
          planes_input = "compute"
          break
        elif choice == '2':
          planes_input = "archive"
          break
        elif choice == '3':
          planes_input = "control,execution"
          break
        elif choice == '4':
          planes_input = "control,execution,compute"
          break
        else:
          print("Invalid choice. Enter 1, 2, 3, or 4.")
    elif tier == "3E":
      print("\nWhat role does this node play in your Tier 3E cluster?")
      print("  [1] Compute node (provides access to large LLMs)")
      print("  [2] Execution node (sandboxes and volatile CI workloads)")
      print("  [3] Control node without runner (control + archive)")
      print("  [4] Control node with runner (control + archive + compute)")
      while True:
        choice = input("Enter choice [1]: ").strip()
        if not choice or choice == '1':
          planes_input = "compute"
          break
        elif choice == '2':
          planes_input = "execution"
          break
        elif choice == '3':
          planes_input = "control,archive"
          break
        elif choice == '4':
          planes_input = "control,archive,compute"
          break
        else:
          print("Invalid choice. Enter 1, 2, 3, or 4.")
    elif tier == "4":
      print("\nWhat role does this node play in your Tier 4 cluster?")
      print("  [1] Compute node (provides access to large LLMs)")
      print("  [2] Execution node (sandboxes and volatile CI workloads)")
      print("  [3] Archive node (vector databases and observability)")
      print("  [4] Control node without runner (control only)")
      print("  [5] Control node with runner (control + compute)")
      while True:
        choice = input("Enter choice [1]: ").strip()
        if not choice or choice == '1':
          planes_input = "compute"
          break
        elif choice == '2':
          planes_input = "execution"
          break
        elif choice == '3':
          planes_input = "archive"
          break
        elif choice == '4':
          planes_input = "control"
          break
        elif choice == '5':
          planes_input = "control,compute"
          break
        else:
          print("Invalid choice. Enter 1, 2, 3, 4, or 5.")

  planes = planes_input.split(',')

  wan_input = args.wan.lower()
  if wan_input not in ['y', 'n', 'yes', 'no']:
    print("\nDo you require remote WAN access to your cluster while traveling,")
    print("or the ability to receive external webhooks (e.g., Telegram bots)?")
    while True:
      wan_choice = input("Require WAN access? [Y/n]: ").strip().lower()
      if wan_choice in ['y', 'yes', '']:
        require_wan = True
        break
      elif wan_choice in ['n', 'no']:
        require_wan = False
        break
  else:
    require_wan = wan_input in ['y', 'yes']

  headless_input = args.headless.lower()
  if headless_input not in ['y', 'n', 'yes', 'no']:
    ts_running = _is_tailscale_running()
    default_hl = 'y' if ts_running else 'n'
    prompt_hl = 'Y/n' if ts_running else 'y/N'

    print("\nIs this machine running as a headless server (no monitor/GUI, accessed via SSH)?")
    while True:
      hl_choice = input(f"Headless server? [{prompt_hl}]: ").strip().lower()
      if hl_choice in ['y', 'yes']:
        is_headless = True
        break
      elif hl_choice in ['n', 'no']:
        is_headless = False
        break
      elif hl_choice == '':
        is_headless = ts_running
        break
  else:
    is_headless = headless_input in ['y', 'yes']

  order_input = args.order
  valid_options = {'safety', 'cost', 'resources'}
  if not order_input:
    default_order = 'cost,safety,resources'
    print("\nPlease specify your priority order for provider selection.")
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
    profile, hostname, tier, planes, hw_details, require_wan, is_headless, order_prefs
  )

  with open(profile_path, 'w') as f:
    json.dump(profile, f, indent=2)

  print(f"\n[Profile] Node '{hostname}' registered as Tier {tier} representing planes: {', '.join(planes)}.")
  wan_str = 'Enabled (Bare-Metal Lifeline)' if require_wan and is_headless else ('Enabled (Dockerized)' if require_wan else 'Disabled')
  print(f"[Profile] Network mesh (Tailscale) set to: {wan_str}")
  prefs_str = ' > '.join([p.capitalize() for p in order_prefs])
  print(f"[Profile] Priorities set to: {prefs_str}")
  print(
    "[Profile] Cluster state updated in profile.json.\n"
    "Run 'make apply' or 'make wizard' to enact changes."
  )

if __name__ == '__main__':
  main()
