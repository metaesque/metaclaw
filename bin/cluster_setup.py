#!/usr/bin/env python3
import os
import json
import socket
import platform
import shutil
import subprocess
import sys
import glob

try:
    from fabric import Connection
except ImportError:
    print("FATAL: Fabric library not found. Run 'make -C bin install-code'.")
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
        "storage_free_gb": round(free_storage / (1024**3), 2),
        "headless": False # Updated interactively in main()
    }

def get_required_ssh_key():
    home = os.path.expanduser("~")
    metaesque_key = os.path.join(home, ".ssh", "id_ed25519_metaesque")
    if not os.path.exists(metaesque_key):
        print(f"FATAL: Required SSH key not found at {metaesque_key}")
        sys.exit(1)
    return metaesque_key

def profile_remote_hardware(ip_address, ssh_user, key_filename):
    try:
        c = Connection(host=ip_address, user=ssh_user, connect_kwargs={"key_filename": key_filename})
        print("  -> Interrogating remote hardware...")
        cmd = """python3 -c "import os, shutil, platform; print(f'{platform.system()}|{platform.machine()}|{os.cpu_count()}|')" """
        res = c.run(cmd, hide=True)
        os_sys, arch, cores, _ = res.stdout.strip().split('|')
        return {"os": os_sys, "architecture": arch, "cpu_cores": int(cores), "headless": True}
    except Exception as e:
        print(f"  -> FATAL: Remote interrogation failed: {e}")
        return {"os": "Linux", "architecture": "x86_64", "headless": True}

def main():
    print("==================================================")
    print(" MetaClaw Distributed Cluster Setup Engine")
    print("==================================================")

    local_host = socket.gethostname()
    local_hw = profile_local_hardware()

    # Prompt for local headless status
    hl = input(f"Is '{local_host}' running headless? [Y/n]: ").strip().lower()
    local_hw['headless'] = True if hl in ['y', '', 'yes'] else False

    print("\nSelect cluster architecture [0, 1, 2]: ")
    tier = input("> ").strip() or "0"

    profile = {"cluster_id": "metaclaw-cluster", "nodes": []}

    # Control Node Registration
    profile["nodes"].append({
        "hostname": local_host, "tier": int(tier),
        "planes": ["control", "execution", "archive"],
        "hardware": local_hw
    })

    if tier == "2":
        print("\nConfiguring Compute Node...")
        host = input("Hostname [compute]: ").strip() or "compute"
        ip = input("IP Address: ").strip()
        user = input("SSH User: ").strip()
        key = get_required_ssh_key()

        hw = profile_remote_hardware(ip, user, key)
        profile["nodes"].append({
            "hostname": host, "tier": 2, "planes": ["compute"],
            "hardware": hw, "ssh_user": user
        })

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
    import metaclaw

    profile = metaclaw.Inst.updateCluster(profile, local_host, int(tier),
                                          profile["nodes"][0]["planes"], local_hw,
                                          True, local_hw['headless'], ["cost"])

    with open("profile.json", "w") as f:
        json.dump(profile, f, indent=2)

    print("\nSUCCESS: profile.json updated.")

if __name__ == "__main__":
    main()
