# ==============================================================================
# META<CLAW> DEVICES API
# ==============================================================================

import os
import json
import socket
import subprocess

def get_hardware_registry():
    """
    Dynamically resolves and parses the hardware.json registry from the global
    METACLAW_CONFIG drop-zone.
    """
    config_dir = os.environ.get('METACLAW_CONFIG')
    if not config_dir:
        # Fallback to scanning .env in the repo root
        lib_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(lib_dir)
        env_path = os.path.join(root_dir, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('METACLAW_CONFIG='):
                        val = line.split('=', 1)[1].strip().strip('"\'')
                        if val and not val.startswith('change_me'):
                            config_dir = val
                        break
        if not config_dir:
            config_dir = os.path.abspath(os.path.join(root_dir, '..', 'config'))

    hw_path = os.path.join(config_dir, 'data', 'hardware.json')
    if os.path.exists(hw_path):
        with open(hw_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_all_devices():
    """
    Returns a dictionary of instantiated Device objects (ComputeNode, PowerStrip, etc.)
    parsed from the central hardware registry.
    """
    data = get_hardware_registry()
    devices = {}
    for uid, dev_data in data.items():
        dtype = dev_data.get('type')
        if dtype == 'compute_node':
            devices[uid] = ComputeNode(uid, dev_data)
        elif dtype == 'power_strip':
            devices[uid] = PowerStrip(uid, dev_data)
        elif dtype == 'external_ssd':
            devices[uid] = ExternalSSD(uid, dev_data)
        elif dtype == 'network_uplink':
            devices[uid] = NetworkUplink(uid, dev_data)
        elif dtype == 'mobile_power':
            devices[uid] = MobilePower(uid, dev_data)
        elif dtype == 'power_asset':
            devices[uid] = PowerAsset(uid, dev_data)
        elif dtype == 'nomadic_client':
            devices[uid] = NomadicClient(uid, dev_data)
        else:
            devices[uid] = Device(uid, dev_data)
    return devices

class Device:
    """
    Base class representing a physical or logical device as defined in hardware.json.
    """
    def __init__(self, uid, data):
        self.uid = uid
        self.data = data
        self.name = data.get("name", uid)
        self.device_type = data.get("type", "unknown")
        self.location = data.get("location", "Unknown")

    def get_info(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "type": self.device_type,
            "location": self.location
        }

class ExternalSSD(Device):
    pass

class NetworkUplink(Device):
    pass

class MobilePower(Device):
    pass

class PowerAsset(Device):
    pass

class NomadicClient(Device):
    pass

class ComputeNode(Device):
    """
    Represents a device capable of providing compute resources (e.g., CPU, GPU).
    """
    def get_hardware_specs(self):
        return {
            "processing": self.data.get("processing", {}),
            "vram": self.data.get("vram", {}),
            "bandwidth_gbps": self.data.get("bandwidth", 0.0)
        }

    def update_data(self):
        """
        Verifies the execution context matches the node identity and executes system
        commands to discover and append real-time hardware telemetry to self.data.
        """
        current_hostname = socket.gethostname().lower()
        if current_hostname not in self.uid.lower() and current_hostname not in self.name.lower():
            raise Exception(f"Execution context mismatch. Cannot update node '{self.uid}' from host '{current_hostname}'.")

        # Gather Block Device Topology
        try:
            res = subprocess.run(['lsblk', '-J', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,UUID'], capture_output=True, text=True)
            if res.returncode == 0:
                self.data['_live_lsblk'] = json.loads(res.stdout)
        except Exception:
            pass

        # Gather USB Bus Topology
        try:
            res = subprocess.run(['lsusb', '-t'], capture_output=True, text=True)
            if res.returncode == 0:
                self.data['_live_lsusb'] = res.stdout.strip()
        except Exception:
            pass

        # Gather System Memory
        try:
            res = subprocess.run(['free', '-m'], capture_output=True, text=True)
            if res.returncode == 0:
                self.data['_live_memory_mb'] = res.stdout.strip()
        except Exception:
            pass

    def mount_storage(self):
        """
        Idempotently maps and mounts SSD volumes defined in the hardware registry.
        """
        mounts = self.data.get("mounts", [])
        for m in mounts:
            mp = m.get("mountpoint")
            uuid = m.get("uuid")
            fstype = m.get("fstype")

            if not mp or not uuid:
                continue

            # Idempotency check: Is it already mounted?
            if os.path.ismount(mp):
                continue

            os.makedirs(mp, exist_ok=True)

            # Execute Mount
            cmd = ['sudo', 'mount']
            if fstype:
                cmd.extend(['-t', fstype])
            cmd.extend([f"UUID={uuid}", mp])

            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to mount UUID {uuid} to {mp}: {e.stderr.decode()}")

class PowerStrip(Device):
    """
    Represents a smart power strip (e.g., Kasa HS300) capable of energy monitoring.
    """
    def get_mac_address(self):
        return self.data.get("mac_address")

    def get_plugs(self):
        return self.data.get("plugs", {})
