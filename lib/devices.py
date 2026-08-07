# ==============================================================================
# META<CLAW> DEVICES API
# ==============================================================================

import os
import json
import socket
import subprocess
import platform
import shutil

def get_hardware_registry():
    """
    Dynamically resolves and parses the individual hardware JSON files
    from the global METACLAW_CONFIG drop-zone.
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

    hardware_dir = os.path.join(config_dir, 'data', 'hardware')
    registry = {}

    if os.path.exists(hardware_dir) and os.path.isdir(hardware_dir):
        for root, dirs, files in os.walk(hardware_dir):
            for file in files:
                if file.endswith('.json'):
                    uid = file[:-5]
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            registry[uid] = data
                    except json.JSONDecodeError:
                        pass
    return registry

def save_device_registry(uid, data):
    """
    Saves an updated device dictionary back to its specific JSON file.
    """
    config_dir = os.environ.get('METACLAW_CONFIG')
    if not config_dir:
        lib_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(lib_dir)
        config_dir = os.path.abspath(os.path.join(root_dir, '..', 'config'))

    hardware_dir = os.path.join(config_dir, 'data', 'hardware')
    if os.path.exists(hardware_dir):
        for root, dirs, files in os.walk(hardware_dir):
            for file in files:
                if file == f"{uid}.json":
                    file_path = os.path.join(root, file)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    return

def get_all_devices():
    """
    Returns a dictionary of instantiated Device objects (ComputeNode, PowerStrip, etc.)
    parsed from the central hardware registry.
    """
    data = get_hardware_registry()
    devices = {}
    for uid, dev_data in data.items():
        dtype = dev_data.get('type')
        if dtype == 'node':
            devices[uid] = ComputeNode(uid, dev_data)
        elif dtype == 'power':
            if 'plugs' in dev_data:
                devices[uid] = PowerStrip(uid, dev_data)
            else:
                devices[uid] = PowerAsset(uid, dev_data)
        elif dtype == 'ssd':
            devices[uid] = ExternalSSD(uid, dev_data)
        elif dtype == 'network':
            devices[uid] = NetworkUplink(uid, dev_data)
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

class PowerAsset(Device):
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
        commands to discover and append real-time hardware telemetry to self.data,
        mirroring the functionality of sysprofile.py.
        """
        current_hostname = socket.gethostname().lower()
        if current_hostname not in self.uid.lower() and current_hostname not in self.name.lower():
            raise Exception(f"Execution context mismatch. Cannot update node '{self.uid}' from host '{current_hostname}'.")

        # 1. OS & Architecture
        self.data['os'] = platform.system()
        self.data['architecture'] = platform.machine()
        self.data['cpu_cores'] = os.cpu_count() or 1

        # 2. Memory Discovery
        try:
            ram_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
            self.data['ram_bytes'] = ram_bytes
            self.data['ram_gb'] = round(ram_bytes / (1024**3), 2)
        except Exception:
            pass

        # 3. Root Storage Discovery
        try:
            total_storage, used_storage, free_storage = shutil.disk_usage('/')
            self.data['storage_total_gb'] = round(total_storage / (1024**3), 2)
            self.data['storage_free_gb'] = round(free_storage / (1024**3), 2)
        except Exception:
            pass

        # 4. Kernel / Uname
        ukeys = ['system', 'node', 'release', 'version', 'machine']
        self.data['uname'] = dict(zip(ukeys + ['processor'], list(platform.uname())))

        # 5. Network Mesh State (Tailscale)
        try:
            res = subprocess.run(['tailscale', 'status'], capture_output=True)
            self.data['tailscale_active'] = (res.returncode == 0)
        except Exception:
            self.data['tailscale_active'] = False

        # 6. GPU & VRAM Discovery
        if self.data['os'] == 'Darwin':
            try:
                res = subprocess.run(['system_profiler', 'SPDisplaysDataType', '-json'], capture_output=True, text=True)
                if res.returncode == 0:
                    d = json.loads(res.stdout)
                    cards = d.get('SPDisplaysDataType', [])
                    if cards:
                        self.data['gpu_detected'] = cards[0].get('sppci_model', 'Apple Silicon')
                        self.data['unified_memory'] = True
            except Exception:
                pass
        elif self.data['os'] == 'Linux':
            try:
                res = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    parts = res.stdout.strip().split('\n')[0].split(',')
                    self.data['gpu_detected'] = parts[0].strip()
                    vram_mb = int(parts[1].replace('MiB', '').strip()) if len(parts) > 1 else 0
                    if vram_mb > 0:
                        self.data['vram_gb'] = round(vram_mb / 1024, 2)
            except Exception:
                pass

        # 7. Block Device Topology (lsblk) -> Populates 'mounts' and 'ssd'
        try:
            res = subprocess.run(['lsblk', '-J', '-b', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,UUID,PHY-SEC,LOG-SEC'], capture_output=True, text=True)
            if res.returncode == 0:
                lsblk_data = json.loads(res.stdout)

                if 'mounts' not in self.data:
                    self.data['mounts'] = []

                def process_blocks(blocks):
                    for b in blocks:
                        name = b.get('name', '')
                        uuid = b.get('uuid')
                        mp = b.get('mountpoint')
                        fstype = b.get('fstype')
                        size = b.get('size', 0)
                        dev_path = f"/dev/{name}"

                        # Populate primary SSD dict if it's the root mount
                        if mp == '/':
                            if 'ssd' not in self.data:
                                self.data['ssd'] = {}
                            if isinstance(size, int):
                                self.data['ssd']['size'] = round(size / (1024**3), 2)

                        # Populate or update the 'mounts' array
                        if uuid and fstype and not name.startswith('loop'):
                            found = False
                            for m in self.data['mounts']:
                                if m.get('uuid') == uuid:
                                    m['device'] = dev_path
                                    m['fstype'] = fstype
                                    if mp:
                                        m['mountpoint'] = mp
                                    if b.get('phy-sec'):
                                        m['physical_sector_size'] = b.get('phy-sec')
                                    if b.get('log-sec'):
                                        m['logical_sector_size'] = b.get('log-sec')
                                    found = True
                                    break
                            if not found:
                                self.data['mounts'].append({
                                    'device': dev_path,
                                    'uuid': uuid,
                                    'fstype': fstype,
                                    'mountpoint': mp,
                                    'physical_sector_size': b.get('phy-sec'),
                                    'logical_sector_size': b.get('log-sec')
                                })

                        if 'children' in b:
                            process_blocks(b['children'])

                process_blocks(lsblk_data.get('blockdevices', []))
        except Exception:
            pass

        # 8. USB Topology (lsusb) -> Tracks active port connection speeds
        try:
            res = subprocess.run(['lsusb', '-t'], capture_output=True, text=True)
            if res.returncode == 0:
                speeds = {'480M': 0, '5000M': 0, '10000M': 0, '20000M': 0, '40000M': 0}
                for line in res.stdout.split('\n'):
                    for s in speeds.keys():
                        if s in line:
                            speeds[s] += 1

                self.data['usb_ports_active'] = [{"speed": k, "connected_devices": v} for k, v in speeds.items() if v > 0]
        except Exception:
            pass

class PowerStrip(Device):
    """
    Represents a smart power strip (e.g., Kasa HS300) capable of energy monitoring.
    """
    def get_mac_address(self):
        return self.data.get("mac_address")

    def get_plugs(self):
        return self.data.get("plugs", {})
