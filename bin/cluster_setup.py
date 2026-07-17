#!/usr/bin/env python3
import os
import json
import socket
import platform
import shutil
import subprocess
import sys

try:
    from fabric import Connection
except ImportError:
    print("FATAL: Fabric library not found. Ensure you have run 'make install-code' in bin/.")
    sys.exit(1)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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
        "storage_free_gb": round(free_storage / (1024**3), 2)
    }

def profile_remote_hardware(ip_address, ssh_user):
    """
    Executes Phase 2 Interrogation via Fabric. Connects over SSH to the remote node,
    harvests actual hardware telemetry securely, and returns a dictionary.
    """
    try:
        print(f"  -> Connecting to {ssh_user}@{ip_address} via Fabric...")
        c = Connection(host=ip_address, user=ssh_user)

        # Gather OS and Arch
        os_sys = c.run('uname -s', hide=True).stdout.strip()
        arch = c.run('uname -m', hide=True).stdout.strip()

        # Gather Memory
        meminfo = c.run("awk '/MemTotal/ {print $2 * 1024}' /proc/meminfo", hide=True).stdout.strip()
        ram_bytes = int(meminfo) if meminfo.isdigit() else 0

        # Gather Storage
        storage_raw = c.run("df -B1 / | awk 'NR==2 {print $2, $4}'", hide=True).stdout.strip().split()
        total_storage = int(storage_raw[0]) if len(storage_raw) == 2 else 0
        free_storage = int(storage_raw[1]) if len(storage_raw) == 2 else 0

        # Gather CPU
        cpu_cores = int(c.run("nproc", hide=True).stdout.strip())

        return {
            "os": os_sys,
            "architecture": arch,
            "ip_address": ip_address,
            "cpu_cores": cpu_cores,
            "ram_gb": round(ram_bytes / (1024**3), 2),
            "storage_total_gb": round(total_storage / (1024**3), 2),
            "storage_free_gb": round(free_storage / (1024**3), 2),
            "headless": True
        }
    except Exception as e:
        print(f"  -> FATAL: Remote interrogation failed: {e}")
        print("  -> Falling back to default baseline estimations.")
        return {
            "os": "Linux",
            "architecture": "x86_64",
            "ip_address": ip_address,
            "headless": True
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

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Setup Engine")
    print("==================================================")

    local_host = socket.gethostname()
    local_hw = profile_local_hardware()

    print(f"\n[Master] Profiling orchestrator node '{local_host}'...")
    print(f"  IP Address: {local_hw['ip_address']}")
    print(f"  RAM capacity: {local_hw['ram_gb']} GB")

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

    if tier_choice == "2":
        profile["nodes"].append({
            "hostname": local_host,
            "tier": 2,
            "planes": ["control", "execution", "archive"],
            "require_wan": True,
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

        print(f"\n[Phase 2] Executing remote hardware interrogation on {compute_host}...")
        compute_hw = profile_remote_hardware(compute_ip, ssh_user)

        # --- PHASE 2: Live SSH Model Pull Execution ---
        print(f"\n[Phase 2] Verifying and pulling required LLMs on remote node.")
        try:
            c = Connection(host=compute_ip, user=ssh_user)
            # pty=True ensures the Ollama progress bar streams naturally to the local terminal
            # without getting buffered by Python's subprocessing layers.
            c.run("OLLAMA_HOST=0.0.0.0:11434 ~/repo/bin/ollama pull ingu627/llama4-scout-q4:109b", pty=True)
            print("  -> Model verification complete.")
        except Exception as e:
            print(f"  -> WARNING: Failed to pull remote models via SSH: {e}")
            print("  -> You may need to pull models manually on the compute node later.")

        profile["nodes"].append({
            "hostname": compute_host,
            "tier": 2,
            "planes": ["compute"],
            "require_wan": True,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": compute_hw
        })
    else:
        profile["nodes"].append({
            "hostname": local_host,
            "tier": int(tier_choice),
            "planes": ["control", "compute", "execution", "archive"],
            "require_wan": False,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })

        # Local model pulling execution for Tier 0 / Tier 1
        print(f"\n[Phase 2] Verifying and pulling required LLMs locally...")
        try:
            subprocess.run(["./bin/ollama", "pull", "gemma4:e4b"], check=False)
            print("  -> Model verification complete.")
        except Exception:
            print("  -> WARNING: Local model pull failed. Ensure Ollama is running.")

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
    import metaclaw

    profile = metaclaw.Inst.updateCluster(
        profile, local_host, int(tier_choice),
        profile["nodes"][0]["planes"], local_hw,
        profile["nodes"][0]["require_wan"], False, ["cost", "safety", "resources"]
    )

    with open("profile.json", "w") as f:
        json.dump(profile, f, indent=2)

    print("\nSUCCESS: Idempotent profile.json compiled successfully.")

    # --- PHASE 3: Broadcast ---
    if tier_choice == "2":
        print(f"\n[Phase 3] Broadcasting unified profile.json to cluster nodes...")
        try:
            c = Connection(host=compute_ip, user=ssh_user)
            # Push the locally generated profile back to the compute node's repo
            c.put("profile.json", "repo/profile.json")
            print(f"  -> Successfully pushed to {compute_host}.")
        except Exception as e:
            print(f"  -> WARNING: Failed to push profile.json: {e}")
            print("  -> Run 'make sync-cluster' manually.")

if __name__ == "__main__":
    main()
