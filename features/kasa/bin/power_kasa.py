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

from devices import get_hardware_registry, save_device_registry
from kasa import Discover, DeviceType, Module

def emit_hardware_metadata(devices):
    """
    Parses hardware.json and emits metadata metrics for physical hosts.
    Used by Grafana to dynamically filter out phantom/legacy hosts.
    """
    for dev_uid, dev_info in devices.items():
        if not isinstance(dev_info, dict):
            continue

        # Ensure we ONLY emit host metadata for actual compute nodes, not SSDs or power strips
        if dev_info.get("type") not in ["node", "compute_node"]:
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

def find_ip_in_arp_table(target_mac):
    """
    Checks the Linux kernel ARP cache (/hostfs/proc/net/arp or /proc/net/arp)
    for a matching MAC address to instantly resolve DHCP IP changes.
    """
    if not target_mac or target_mac == "UNKNOWN":
        return None
    target_norm = target_mac.upper().replace("-", ":")
    for arp_path in ["/hostfs/proc/net/arp", "/proc/net/arp"]:
        if os.path.exists(arp_path):
            try:
                with open(arp_path, "r") as f:
                    for line in f.readlines()[1:]:
                        parts = line.split()
                        if len(parts) >= 4:
                            ip_addr, _, _, hw_addr = parts[0], parts[1], parts[2], parts[3]
                            if hw_addr.upper().replace("-", ":") == target_norm:
                                return ip_addr
            except Exception:
                pass
    return None

async def sweep_subnet_for_kasa(subnet_prefix="10.0.0."):
    """
    Executes a fast, bounded concurrent unicast discovery sweep across a /24 LAN
    subnet when a router's DHCP lease moves a Kasa strip to a new IP and blocks
    255.255.255.255 broadcast discovery.
    """
    sem = asyncio.Semaphore(64)
    discovered = {}

    async def probe(host_ip):
        async with sem:
            try:
                dev = await Discover.discover_single(host_ip, timeout=1)
                if dev and dev.device_type == DeviceType.Strip:
                    discovered[host_ip] = dev
            except Exception:
                pass

    await asyncio.gather(*(probe(f"{subnet_prefix}{i}") for i in range(1, 255)))
    return discovered

async def run_telegraf_export():
    # Fast-fail constraint: Kasa discovery only needs to run on one node to prevent
    # duplicate network polling. We restrict this entirely to the Control Plane.
    if not is_control_plane():
        sys.exit(0)

    devices = get_hardware_registry()

    # Establish the valid Grafana dashboard variables
    emit_hardware_metadata(devices)

    found_devices = {}
    unresolved_strips = []

    # Tier 1: Unicast discovery based on hardware registry IPs (or ARP table lookup)
    for dev_uid, dev_info in devices.items():
        if isinstance(dev_info, dict) and dev_info.get("type") in ["power", "power_strip"] and "plugs" in dev_info:
            ip = dev_info.get("ip_address")
            mac = dev_info.get("mac_address", "").upper().replace("-", ":")

            if ip:
                try:
                    dev = await Discover.discover_single(ip, timeout=2)
                    if dev and dev.device_type == DeviceType.Strip:
                        found_devices[ip] = dev
                        continue
                except Exception as e:
                    print(f"Error discovering Kasa device at {ip}: {e}", file=sys.stderr)

            # Check ARP cache if configured IP timed out or was omitted
            arp_ip = find_ip_in_arp_table(mac)
            if arp_ip and arp_ip != ip:
                try:
                    dev = await Discover.discover_single(arp_ip, timeout=2)
                    if dev and dev.device_type == DeviceType.Strip:
                        print(f"[Kasa Self-Heal] Discovered {dev_uid} ({mac}) via ARP at new IP {arp_ip}", file=sys.stderr)
                        found_devices[arp_ip] = dev
                        continue
                except Exception:
                    pass

            unresolved_strips.append((dev_uid, dev_info))

    # Tier 2 & 3: Broadcast fallback + fast concurrent /24 subnet unicast sweep if any strip is unresolved
    if unresolved_strips:
        try:
            bcast_devs = await Discover.discover(timeout=2)
            for b_ip, b_dev in bcast_devs.items():
                if b_dev.device_type == DeviceType.Strip:
                    found_devices[b_ip] = b_dev
        except Exception:
            pass

        if len(found_devices) < len(unresolved_strips):
            # Determine subnet prefix from configured IP (defaulting to 10.0.0.)
            sample_ip = unresolved_strips[0][1].get("ip_address", "10.0.0.1")
            prefix = ".".join(sample_ip.split(".")[:3]) + "." if "." in sample_ip else "10.0.0."
            swept_devs = await sweep_subnet_for_kasa(prefix)
            for s_ip, s_dev in swept_devs.items():
                found_devices[s_ip] = s_dev
                print(f"[Kasa Self-Heal] Located Kasa strip ({s_dev.mac}) via subnet sweep at {s_ip}", file=sys.stderr)

    strip_ips = list(found_devices.keys())

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
            # Check for either 'power_strip' or 'power' (with a 'plugs' array) to correctly identify the strip
            if isinstance(dev_info, dict) and dev_info.get("type") in ["power", "power_strip"] and "plugs" in dev_info:
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
    asyncio.run(run_telegraf_export())
