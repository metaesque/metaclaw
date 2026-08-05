"""
Purpose: Monitor Kasa HS300 power strips and host metrics.
Outputs telemetry in Influx Line Protocol format.
"""

import asyncio
import os
import sys
import json
import socket

# Dynamically append the lib directory to the path so we can import MetaClaw tools
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "lib"))
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

try:
    from metaclaw import Inst
except ImportError as e:
    print(f"Error importing metaclaw: {e}", file=sys.stderr)
    Inst = None

from kasa import Discover, DeviceType, Module

def load_hardware_config(config_path):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)

def emit_hardware_metadata(devices):
    """
    Parses hardware.json and emits metadata metrics for physical hosts.
    Used by Grafana to dynamically filter out phantom/legacy hosts.
    """
    for dev_uid, dev_info in devices.items():
        if not isinstance(dev_info, dict):
            continue

        # Safely traverse the nested dictionary: price -> purchased -> date
        price = dev_info.get("price") or {}
        purchased = price.get("purchased") or {}
        date = purchased.get("date")

        # If the device has a valid purchase date, it is a real physical node
        if date is not None:
            # Emits: host_metadata_active{host="compute"} 1
            print(f"host_metadata,host={dev_uid} active=1i")

def is_control_plane():
    """
    Determines if the current host implements the 'control' plane.
    """
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    profile_path = os.path.join(repo_root, "profile.json")

    if not os.path.exists(profile_path):
        return True # Fail-safe to ensure we don't lose data if profile is missing

    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)

            # Gather all possible network identities for this machine
            local_identities = {socket.gethostname().lower()}
            if "HOST_IDENTIFIER" in os.environ:
                local_identities.add(os.environ["HOST_IDENTIFIER"].lower())

            # Telegraf natively mounts the host's root filesystem to /hostfs
            try:
                with open('/hostfs/etc/hostname', 'r') as hf:
                    local_identities.add(hf.read().strip().lower())
            except Exception:
                pass

            for node in profile.get("nodes", []):
                node_hostname = node.get("hostname", "").lower()
                node_ip = node.get("hardware", {}).get("ip_address", "").lower()

                if node_hostname in local_identities or (node_ip and node_ip in local_identities):
                    if "control" in node.get("planes", []):
                        return True
    except Exception as e:
        print(f"Error parsing profile.json: {e}", file=sys.stderr)

    return False

async def run_telegraf_export(config_path):
    # Fast-fail constraint: Kasa discovery only needs to run on one node to prevent
    # duplicate network polling. We restrict this entirely to the Control Plane.
    if not is_control_plane():
        sys.exit(0)

    devices = load_hardware_config(config_path)

    # Establish the valid Grafana dashboard variables
    emit_hardware_metadata(devices)

    try:
        found_devices = await Discover.discover(timeout=5)
    except Exception as e:
        print(f"Error during Kasa discovery: {e}", file=sys.stderr)
        return

    strip_ips = [
        ip for ip, dev in found_devices.items()
        if dev.device_type == DeviceType.Strip
    ]

    for ip in strip_ips:
        kasa_dev = found_devices[ip]
        try:
            await kasa_dev.update()
        except Exception as e:
            print(f"Error updating Kasa device at {ip}: {e}", file=sys.stderr)
            continue

        mac = kasa_dev.mac.upper().replace("-", ":")

        strip_plugs = {}
        for dev_uid, dev_info in devices.items():
            if isinstance(dev_info, dict) and dev_info.get("type") == "power_strip":
                hw_mac = dev_info.get("mac_address", "").upper().replace("-", ":")
                if hw_mac == mac:
                    strip_plugs = dev_info.get("plugs", {})
                    break

        for plug_idx, plug in enumerate(kasa_dev.children):
            energy = plug.modules[Module.Energy]
            power = float(
                getattr(
                    energy, 'current_consumption', getattr(energy, 'power', 0.0)
                )
            )
            voltage = float(energy.voltage)
            current = float(energy.current)

            dev_uid = strip_plugs.get(str(plug_idx), "empty")

            print(
                f"kasa_power,device={dev_uid} "
                f"watts={power:.3f},volts={voltage:.3f},amps={current:.3f}"
            )

if __name__ == "__main__":
    candidates = [
        os.path.join(script_dir, "..", "data", "hardware.json"),
        os.path.join(script_dir, "..", "..", "..", "workspace", "src", "data", "hardware.json"),
    ]
    cfg_path = next((c for c in candidates if os.path.exists(c)), candidates[0])
    asyncio.run(run_telegraf_export(cfg_path))
