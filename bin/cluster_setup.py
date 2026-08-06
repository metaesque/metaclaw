#!/usr/bin/env python3
import os
import sys

# Ensure sysprofile can be imported from the local bin directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import sysprofile

import json
import socket
import platform
import shutil
import subprocess

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

def get_local_tailscale_ip():
    """
    Queries the local Tailscale daemon directly for this machine's 100.x.y.z IP address,
    bypassing hostname matching entirely.
    """
    try:
        res = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            self_ips = data.get('Self', {}).get('TailscaleIPs', [])
            if self_ips:
                return self_ips[0]
    except Exception:
        pass
    return ""

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

def run_remote(ip_address, ssh_user, key_filename, cmd, hide=False, prefix=""):
    """
    Executes a remote command using the native OpenSSH client via subprocess.
    This safely bypasses Paramiko's inability to negotiate Tailscale's 'none' auth.
    Supports native TTY allocation to ensure remote interactive prompts do not hang.
    """
    ssh_cmd = [
        "ssh", "-i", key_filename,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR"
    ]

    # Force pseudo-terminal allocation for interactive prompt visibility
    if not hide:
        ssh_cmd.append("-t")

    ssh_cmd.extend([f"{ssh_user}@{ip_address}", cmd])

    if hide:
        return subprocess.run(ssh_cmd, capture_output=True, text=True)
    else:
        if prefix:
            print(f"\n--- [Remote Stream: {prefix}] ---", flush=True)

        # Execute natively so stdin/stdout map directly to the user's terminal
        process = subprocess.run(ssh_cmd)

        if prefix:
            print(f"--- [End Stream: {prefix}] ---\n", flush=True)

        class Result:
            def __init__(self, returncode):
                self.returncode = returncode
                self.stderr = ""
        return Result(process.returncode)

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

        print("  -> Syncing local sysprofile.py to remote node...")
        sysprofile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sysprofile.py")
        scp_remote(ip_address, ssh_user, key_filename, sysprofile_path, "repo/bin/sysprofile.py")

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
    find the Tailscale IP address associated with the requested hostname or alias.
    """
    try:
        res = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        target_clean = target_hostname.lower().split('.')[0]

        self_info = data.get('Self', {})
        self_host = self_info.get('HostName', '').lower().split('.')[0]
        self_dns = self_info.get('DNSName', '').lower().split('.')[0]
        if target_clean in [self_host, self_dns]:
            ips = self_info.get('TailscaleIPs', [])
            if ips:
                return ips[0]

        for peer_key, peer_info in data.get('Peer', {}).items():
            p_host = peer_info.get('HostName', '').lower().split('.')[0]
            p_dns = peer_info.get('DNSName', '').lower().split('.')[0]
            if target_clean in [p_host, p_dns]:
                ips = peer_info.get('TailscaleIPs', [])
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

    # -------------------------------------------------------------------------
    # TAILSCALE AUTH KEY SYNCHRONIZATION
    # -------------------------------------------------------------------------
    ts_env_dir = os.path.join("services", "networks", "tailscale")
    local_ts_json = os.path.join(ts_env_dir, ".env.json")
    ts_data = {}
    if os.path.exists(local_ts_json):
        try:
            with open(local_ts_json, "r") as f:
                ts_data = json.load(f)
        except:
            pass

    ts_key = ts_data.get("TAILSCALE_AUTHKEY", "")
    ts_input = input(f"  -> Enter TAILSCALE_AUTHKEY [{ts_key or 'None'}]: ").strip()
    if ts_input:
        ts_key = ts_input

    if ts_key:
        ts_data["TAILSCALE_AUTHKEY"] = ts_key
        os.makedirs(ts_env_dir, exist_ok=True)
        with open(local_ts_json, "w") as f:
            json.dump(ts_data, f, indent=2)

    # Broadcast secrets to other nodes via jq merging
    for node in profile.get("nodes", []):
        if node["hostname"] != socket.gethostname() and (node.get("tier") == 2 or node.get("tier") == 4):
            ip = node["hardware"]["ip_address"]
            user = node.get("ssh_user", os.getlogin())
            print(f"  -> Pushing secrets to {node['hostname']} ({ip})...")

            # This complex jq string safely creates the proxy file if missing, then merges the keys
            jq_cmd = f"mkdir -p ~/repo/services/proxies/litellm && " \
                     f"touch ~/repo/services/proxies/litellm/.env.json && " \
                     f"jq -n 'inputs | .ACTIVE_PROXY_KEY=\"{active_key}\" | .GEMINI_API_KEY=\"{gemini_key}\"' " \
                     f"~/repo/services/proxies/litellm/.env.json > ~/repo/tmp_env.json 2>/dev/null || " \
                     f"echo '{{\"ACTIVE_PROXY_KEY\":\"{active_key}\",\"GEMINI_API_KEY\":\"{gemini_key}\"}}' > ~/repo/tmp_env.json && " \
                     f"mv ~/repo/tmp_env.json ~/repo/services/proxies/litellm/.env.json"

            res = run_remote(ip, user, ssh_key, jq_cmd, hide=True)
            if res.returncode != 0:
                print(f"  -> WARNING: Failed to push Proxy secrets. Is jq installed on the remote host? Error: {res.stderr}")

            if ts_key:
                ts_jq_cmd = f"mkdir -p ~/repo/services/networks/tailscale && " \
                            f"touch ~/repo/services/networks/tailscale/.env.json && " \
                            f"jq -n 'inputs | .TAILSCALE_AUTHKEY=\"{ts_key}\"' " \
                            f"~/repo/services/networks/tailscale/.env.json > ~/repo/tmp_ts.json 2>/dev/null || " \
                            f"echo '{{\"TAILSCALE_AUTHKEY\":\"{ts_key}\"}}' > ~/repo/tmp_ts.json && " \
                            f"mv ~/repo/tmp_ts.json ~/repo/services/networks/tailscale/.env.json"
                res_ts = run_remote(ip, user, ssh_key, ts_jq_cmd, hide=True)
                if res_ts.returncode != 0:
                    print(f"  -> WARNING: Failed to push Tailscale secrets.")

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Setup Engine")
    print("==================================================")

    # 1. Profile the local orchestrating node
    local_host = socket.gethostname()
    local_hw = sysprofile.platform_details()

    # Query local Tailscale daemon directly to override LAN IP with 100.x.y.z
    ts_ip = get_local_tailscale_ip()
    if ts_ip:
        local_hw['ip_address'] = ts_ip
        local_hw['tailscale_active'] = True

    print(f"\n[Master] Profiling orchestrator node '{local_host}'...")
    print(f"  IP Address: {local_hw['ip_address']}")
    print(f"  OS RAM capacity: {local_hw['ram_gb']} GB")
    print(f"  Hardware RAM detected: {local_hw.get('ram_hardware_gb')} GB")
    print(f"  Native Tailscale Active: {local_hw.get('tailscale_active', False)}")

    # Explicit headless prompt to defeat dummy plug heuristics
    default_hl = 'y' if local_hw.get('tailscale_active') else 'n'
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

    # Routine Strategy Configuration
    print("\nSelect Prompt Routing Strategy for OpenClaw:")
    print("  [1] Lexical + Predictive (Uses local Judge Model to score complexity)")
    print("  [2] Pass-Through (Rigid 1:1 mapping based entirely on YAML profiles)")
    print("  [3] Semantic-Predictive (Hybrid Vector + LLM Judge Routing)")
    while True:
        r_choice = input("Enter choice [1]: ").strip()
        if not r_choice or r_choice == '1':
            routing_strategy = "lexical_predictive"
            break
        elif r_choice == '2':
            routing_strategy = "pass_through"
            break
        elif r_choice == '3':
            routing_strategy = "semantic_predictive"
            break
        else:
            print("Invalid choice.")

    profile["routing_strategy"] = routing_strategy

    if routing_strategy == "semantic_predictive":
        print("\nSelect Semantic Granularity:")
        print("  [1] Hierarchical Semantic Routing (Only Team Leads added to vector space)")
        print("  [2] Flat Semantic Routing (All team members and leads added to vector space)")
        while True:
            g_choice = input("Enter choice [1]: ").strip()
            if not g_choice or g_choice == '1':
                semantic_granularity = "hierarchical"
                break
            elif g_choice == '2':
                semantic_granularity = "flat"
                break
            else:
                print("Invalid choice.")
        profile["semantic_granularity"] = semantic_granularity
        print(f"  -> Semantic Granularity saved: {semantic_granularity}")

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

        ssh_key = get_required_ssh_key()
        print(f"Using enforced SSH identity: {ssh_key}")

        while True:
            print("\nEnter remote Compute node network coordinates:")
            compute_host = input("Compute Node Hostname [compute]: ").strip() or "compute"

            default_ip = get_tailscale_ip(compute_host)
            ip_prompt = f"Compute Node IP address [{default_ip}]: " if default_ip else "Compute Node IP address (e.g., 100.x.y.z): "
            compute_ip = input(ip_prompt).strip()
            if not compute_ip and default_ip:
                compute_ip = default_ip

            current_user = os.getlogin()
            ssh_user = input(f"SSH Username for remote connection [{current_user}]: ").strip() or current_user

            print(f"\n[Phase 2] Executing remote hardware interrogation on {compute_host}...")
            compute_hw = profile_remote_hardware(compute_ip, ssh_user, ssh_key)

            print(f"\n[Hardware Verification] Node: {compute_host}")
            print(f"  Detected OS RAM: {compute_hw.get('ram_gb')} GB")
            print(f"  Detected Hardware RAM: {compute_hw.get('ram_hardware_gb')} GB")
            print(f"  Detected GPU: {compute_hw.get('gpu_detected')}")

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

            add_another = input("\nAdd another Compute node to the cluster? [y/N]: ").strip().lower()
            if add_another not in ['y', 'yes']:
                break
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
        print(f"\n[Phase 3] Broadcasting unified profile.json to all cluster nodes...")
        for node in profile.get("nodes", []):
            if node["hostname"] != socket.gethostname():
                ip = node["hardware"]["ip_address"]
                user = node.get("ssh_user", os.getlogin())
                res = scp_remote(ip, user, ssh_key, "profile.json", "repo/profile.json")
                if res.returncode == 0:
                    print(f"  -> Successfully pushed to {node['hostname']}.")
                else:
                    print(f"  -> WARNING: Failed to push to {node['hostname']}: {res.stderr}")
                    print("  -> Run 'make sync-cluster' manually later.")

    # --- PHASE 4: Global Secrets ---
    configure_env_secrets(profile, ssh_key)

    # --- PHASE 5: Remote Execution Pipeline ---
    print("\n[Phase 5] Executing remote cluster setup tasks...")
    for node in profile.get("nodes", []):
        if node["hostname"] != socket.gethostname():
            ip = node["hardware"]["ip_address"]
            user = node.get("ssh_user", os.getlogin())
            print(f"  -> Triggering 'make setup-local' on remote node {node['hostname']} ({ip})...")
            # Using run_remote with hide=False inherits the TTY and displays interactive streams natively
            res = run_remote(ip, user, ssh_key, "cd ~/repo && make setup-local", hide=False, prefix=node['hostname'])
            if res.returncode != 0:
                print(f"  -> WARNING: Remote setup failed on {node['hostname']}.")

    print("\nCluster configuration complete. Proceed by running: make wizard-cluster")

if __name__ == "__main__":
    main()
