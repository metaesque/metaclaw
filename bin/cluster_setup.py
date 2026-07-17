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

def get_tailscale_ip(target_hostname):
    """
    Executes 'tailscale status --json' and parses the output to dynamically
    find the Tailscale IP address associated with the requested hostname.
    """
    try:
        res = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        # Search the Peer dictionary
        for peer_key, peer_info in data.get('Peer', {}).items():
            host = peer_info.get('HostName', '')
            if host.lower() == target_hostname.lower():
                ips = peer_info.get('TailscaleIPs', [])
                if ips:
                    return ips[0]

        # Fallback: check if the target is actually the local machine itself
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

    # 1. Profile the local orchestrating node
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
        # Master node serves strictly as Control Plane in Tier 2
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

        # Interrogate Tailscale for an IP match
        default_ip = get_tailscale_ip(compute_host)
        ip_prompt = f"Compute Node IP address [{default_ip}]: " if default_ip else "Compute Node IP address (e.g., 100.x.y.z): "

        compute_ip = input(ip_prompt).strip()
        if not compute_ip and default_ip:
            compute_ip = default_ip

        # Inject compute node configuration shell using basic interrogation targets
        profile["nodes"].append({
            "hostname": compute_host,
            "tier": 2,
            "planes": ["compute"],
            "require_wan": True,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": {
                "os": "Linux",
                "architecture": "x86_64",
                "ip_address": compute_ip,
                "headless": True
            }
        })
        # TODO [Phase 2]: Implement interactive SSH session via Fabric to pull down required
        # local models (e.g. gemma4:e4b, llama4:109b) directly to the compute node
        # ensuring the Daemon is fully provisioned before closing the setup loop.
    else:
        # Tiers 0 & 1 execute entirely locally on shared hardware
        profile["nodes"].append({
            "hostname": local_host,
            "tier": int(tier_choice),
            "planes": ["control", "compute", "execution", "archive"],
            "require_wan": False,
            "order_prefs": ["cost", "safety", "resources"],
            "hardware": local_hw
        })
        # TODO [Phase 2]: Implement local subprocess shell commands to pull required models
        # directly via Ollama CLI.

    # Execute dynamic local update pass via inherited orchestrator library
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
    print("If operating a Tier 2 infrastructure, run 'make sync-cluster' to distribute state.")

if __name__ == "__main__":
    main()
