#!/usr/bin/env python3
import os
import json
import socket
import platform
import shutil
import subprocess
import sys

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_tailscale_active():
    """
    Checks if the Tailscale daemon is currently running on the host OS.
    """
    try:
        res = subprocess.run(['tailscale', 'status'], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def profile_local_hardware():
    total_storage, _, free_storage = shutil.disk_usage('/')
    try:
        ram_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    except Exception:
        ram_bytes = 0

    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "ip_address": get_local_ip(),
        "cpu_cores": os.cpu_count() or 1,
        "ram_gb": round(ram_bytes / (1024**3), 2),
        "storage_total_gb": round(total_storage / (1024**3), 2),
        "storage_free_gb": round(free_storage / (1024**3), 2),
        "tailscale_active": is_tailscale_active(),
        "headless": False # Updated interactively
    }

def get_required_ssh_key():
    """
    Ensures the strict use of the MetaClaw deployment key.
    """
    home = os.path.expanduser("~")
    metaesque_key = os.path.join(home, ".ssh", "id_ed25519_metaesque")

    if not os.path.exists(metaesque_key):
        print(f"FATAL: Required SSH key not found at {metaesque_key}")
        print("Ensure bin/setup_plane.sh was executed properly.")
        sys.exit(1)

    return metaesque_key

def run_remote(ip_address, ssh_user, key_filename, cmd, hide=False):
    """
    Executes a remote command using the native OpenSSH client via subprocess.
    This safely bypasses Paramiko's inability to negotiate Tailscale's 'none' auth.
    """
    ssh_cmd = [
        "ssh", "-i", key_filename,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        f"{ssh_user}@{ip_address}",
        cmd
    ]
    if hide:
        return subprocess.run(ssh_cmd, capture_output=True, text=True)
    else:
        return subprocess.run(ssh_cmd)

def scp_remote(ip_address, ssh_user, key_filename, src, dst):
    """
    Transfers a file using the native SCP client.
    """
    scp_cmd = [
        "scp", "-i", key_filename,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        src,
        f"{ssh_user}@{ip_address}:{dst}"
    ]
    return subprocess.run(scp_cmd, capture_output=True, text=True)

def profile_remote_hardware(ip_address, ssh_user, key_filename):
    """
    Executes Phase 2 Interrogation via native SSH, bootstrapping the remote
    Python environment and invoking the remote sysprofile.py script.
    """
    try:
        print(f"  -> Connecting to {ssh_user}@{ip_address} via native SSH...")

        print("  -> Bootstrapping remote Python environment...")
        run_remote(ip_address, ssh_user, key_filename, "cd ~/repo && make -C bin install-code > /dev/null 2>&1", hide=True)

        print("  -> Executing remote sysprofile.py...")
        # Use a python one-liner over SSH to import the remote sysprofile module and dump the dict
        cmd = """cd ~/repo && bin/.venv/bin/python -c "import sys; sys.path.insert(0, 'bin'); import sysprofile; import json; print(json.dumps(sysprofile.platform_details()))" """
        res = run_remote(ip_address, ssh_user, key_filename, cmd, hide=True)

        if res.returncode != 0:
            raise Exception(res.stderr.strip())

        hw_details = json.loads(res.stdout.strip())
        return hw_details

    except Exception as e:
        print(f"  -> FATAL: Remote interrogation failed: {e}")
        print("  -> Falling back to default baseline estimations.")
        return {
            "os": "Linux",
            "architecture": "x86_64",
            "ip_address": ip_address,
            "tailscale_active": True
        }

def get_tailscale_ip(target_hostname):
    """
    Executes 'tailscale status --json' and parses the output to dynamically
    find the Tailscale IP address associated with the requested hostname.
    """
    try:
        res = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        for peer_key, peer_info in data.get('Peer', {}).items():
            host = peer_info.get('HostName', '')
            if host.lower() == target_hostname.lower():
                ips = peer_info.get('TailscaleIPs', [])
                if ips:
                    return ips[0]

        self_info = data.get('Self', {})
        if self_info.get('HostName', '').lower() == target_hostname.lower():
            ips = self_info.get('TailscaleIPs', [])
            if ips:
                return ips[0]

    except Exception:
        pass

    return ""

def configure_env_secrets(profile, ssh_key=None):
    """
    Phase 4: Establishes global secrets locally, then uses SSH and jq to safely
    merge them into the remote nodes' .env.json files without destroying local overrides.
    """
    print("\n[Phase 4] Configuring Global Secrets (.env.json)...")
    import secrets
    import string

    def gen_pwd():
        return "sk-" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

    litellm_env_dir = os.path.join("services", "proxies", "litellm")
    local_env_json = os.path.join(litellm_env_dir, ".env.json")

    env_data = {}
    if os.path.exists(local_env_json):
        try:
            with open(local_env_json, "r") as f:
                env_data = json.load(f)
        except:
            pass

    active_key = env_data.get("ACTIVE_PROXY_KEY")
    gemini_key = env_data.get("GEMINI_API_KEY", "")

    if not active_key or "change_me" in active_key:
        active_key = gen_pwd()
        print(f"  -> Generated new ACTIVE_PROXY_KEY: {active_key}")
    else:
        print("  -> ACTIVE_PROXY_KEY already exists. Preserving.")

    gemini_input = input(f"  -> Enter GEMINI_API_KEY [{gemini_key or 'None'}]: ").strip()
    if gemini_input:
        gemini_key = gemini_input

    env_data["ACTIVE_PROXY_KEY"] = active_key
    env_data["GEMINI_API_KEY"] = gemini_key

    os.makedirs(litellm_env_dir, exist_ok=True)
    with open(local_env_json, "w") as f:
        json.dump(env_data, f, indent=2)

    # Broadcast secrets to other nodes via jq merging
    for node in profile.get("nodes", []):
        if node["hostname"] != socket.gethostname() and node.get("tier") == 2:
            ip = node["hardware"]["ip_address"]
            user = node.get("ssh_user", os.getlogin())
            print(f"  -> Pushing secrets to {node['hostname']} ({ip})...")

            # This complex jq string safely creates the file if missing, then merges the keys
            jq_cmd = f"mkdir -p ~/repo/services/proxies/litellm && " \
                     f"touch ~/repo/services/proxies/litellm/.env.json && " \
                     f"jq -n 'inputs | .ACTIVE_PROXY_KEY=\"{active_key}\" | .GEMINI_API_KEY=\"{gemini_key}\"' " \
                     f"~/repo/services/proxies/litellm/.env.json > ~/repo/tmp_env.json 2>/dev/null || " \
                     f"echo '{{\"ACTIVE_PROXY_KEY\":\"{active_key}\",\"GEMINI_API_KEY\":\"{gemini_key}\"}}' > ~/repo/tmp_env.json && " \
                     f"mv ~/repo/tmp_env.json ~/repo/services/proxies/litellm/.env.json"

            res = run_remote(ip, user, ssh_key, jq_cmd, hide=True)
            if res.returncode != 0:
                print(f"  -> WARNING: Failed to push secrets. Is jq installed on the remote host? Error: {res.stderr}")

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Setup Engine")
    print("==================================================")

    # 1. Profile the local orchestrating node
    local_host = socket.gethostname()
    local_hw = profile_local_hardware()

    print(f"\n[Master] Profiling orchestrator node '{local_host}'...")
    print(f"  IP Address: {local_hw['ip_address']}")
    print(f"  RAM capacity: {local_hw['ram_gb']} GB")
    print(f"  Native Tailscale Active: {local_hw['tailscale_active']}")

    # Explicit headless prompt to defeat dummy plug heuristics
    default_hl = 'y' if local_hw['tailscale_active'] else 'n'
    hl_input = input(f"Is orchestrator node '{local_host}' running headless? [{default_hl}]: ").strip().lower()
    local_hw['headless'] = True if hl_input in ['y', 'yes'] else (False if hl_input in ['n', 'no'] else default_hl == 'y')

    print("\nConfigure Cluster Topology:")
    print("  [0] Tier 0: Single Laptop Minilith (Constrained Context)")
    print("  [1] Tier 1: Single Mini-PC Monolith (All-In-One Node)")
    print("  [2] Tier 2: Data Sovereignty Farm (Split Control + Compute Nodes)")

    while True:
        tier_choice = input("Select cluster architecture [0]: ").strip() or "0"
        if tier_choice in ["0", "1", "2"]:
            break
        print("Invalid allocation tier choice.")

    profile = {
        "cluster_id": f"metaclaw-cluster-centralized",
        "routing_strategy": "lexical_predictive",
        "nodes": []
    }

    ssh_key = None
    if tier_choice == "2":
        profile["nodes"].append({
            "hostname": local_host,
            "tier": 2,
            "planes": ["control", "execution", "archive"],
            "require_wan": True,
            "ssh_user": os.getlogin(),
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })

        print("\nEnter remote Compute node network coordinates:")
        compute_host = input("Compute Node Hostname [compute]: ").strip() or "compute"

        default_ip = get_tailscale_ip(compute_host)
        ip_prompt = f"Compute Node IP address [{default_ip}]: " if default_ip else "Compute Node IP address (e.g., 100.x.y.z): "
        compute_ip = input(ip_prompt).strip()
        if not compute_ip and default_ip:
            compute_ip = default_ip

        current_user = os.getlogin()
        ssh_user = input(f"SSH Username for remote connection [{current_user}]: ").strip() or current_user

        ssh_key = get_required_ssh_key()
        print(f"Using enforced SSH identity: {ssh_key}")

        print(f"\n[Phase 2] Executing remote hardware interrogation on {compute_host}...")
        compute_hw = profile_remote_hardware(compute_ip, ssh_user, ssh_key)

        # CRITICAL FIX: Overwrite the hardware IP returned by sysprofile (which is the LAN IP)
        # with the explicitly resolved Tailscale IP, so all downstream orchestration uses Tailscale SSH.
        compute_hw['ip_address'] = compute_ip

        c_default_hl = 'y' if compute_hw.get('tailscale_active') else 'y'
        c_hl_input = input(f"Is Compute node '{compute_host}' running headless? [{c_default_hl}]: ").strip().lower()
        compute_hw['headless'] = True if c_hl_input in ['y', 'yes'] else (False if c_hl_input in ['n', 'no'] else c_default_hl == 'y')

        profile["nodes"].append({
            "hostname": compute_host,
            "tier": 2,
            "planes": ["compute"],
            "require_wan": True,
            "ssh_user": ssh_user,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": compute_hw
        })
    else:
        profile["nodes"].append({
            "hostname": local_host,
            "tier": int(tier_choice),
            "planes": ["control", "compute", "execution", "archive"],
            "require_wan": False,
            "ssh_user": os.getlogin(),
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
    import metaclaw

    profile = metaclaw.Inst.updateCluster(
        profile, local_host, int(tier_choice),
        profile["nodes"][0]["planes"], local_hw,
        True if tier_choice == "2" else False, local_hw['headless'], ["cost", "safety", "resources"]
    )

    with open("profile.json", "w") as f:
        json.dump(profile, f, indent=2)

    print("\nSUCCESS: Idempotent profile.json compiled successfully.")

    # --- PHASE 3: Broadcast ---
    if tier_choice == "2":
        print(f"\n[Phase 3] Broadcasting unified profile.json to cluster nodes...")
        res = scp_remote(compute_ip, ssh_user, ssh_key, "profile.json", "repo/profile.json")
        if res.returncode == 0:
            print(f"  -> Successfully pushed to {compute_host}.")
        else:
            print(f"  -> WARNING: Failed to push profile.json: {res.stderr}")
            print("  -> Run 'make sync-cluster' manually.")

    # --- PHASE 4: Global Secrets ---
    configure_env_secrets(profile, ssh_key)

    print("\nCluster configuration complete. Proceed by running: make wizard-cluster")

if __name__ == "__main__":
    main()
