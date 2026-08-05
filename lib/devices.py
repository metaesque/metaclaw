# ==============================================================================
# META<CLAW> DEVICES API
# ==============================================================================

import os
import json

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

class PowerStrip(Device):
    """
    Represents a smart power strip (e.g., Kasa HS300) capable of energy monitoring.
    """
    def get_mac_address(self):
        return self.data.get("mac_address")

    def get_plugs(self):
        return self.data.get("plugs", {})
