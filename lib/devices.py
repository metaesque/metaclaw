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

        # 9. Nomadic External SSD Tracking
        try:
            from lib import metaclaw
            all_devices = metaclaw.Inst.devices()
            attached_uuids = set()
            res = subprocess.run(['lsblk', '-J', '-o', 'UUID'], capture_output=True, text=True)
            if res.returncode == 0:
                lsblk_data = json.loads(res.stdout)
                def extract_uuids(blocks):
                    for b in blocks:
                        if b.get('uuid'):
                            attached_uuids.add(b['uuid'].upper())
                            attached_uuids.add(b['uuid'].lower())
                        if 'children' in b:
                            extract_uuids(b['children'])
                extract_uuids(lsblk_data.get('blockdevices', []))

                for uid, dev in all_devices.items():
                    if dev.device_type == 'ssd':
                        for m in dev.data.get('mounts', []):
                            uuid = m.get('uuid')
                            if uuid and (uuid.upper() in attached_uuids or uuid.lower() in attached_uuids):
                                if dev.data.get('current_host') != self.uid:
                                    dev.data['current_host'] = self.uid
                                    save_device_registry(uid, dev.data)
                                    print(f"Registered nomadic SSD '{uid}' as physically attached to {self.uid}.")
        except Exception as e:
            print(f"DIAGNOSTIC: Failed to track nomadic SSDs: {e}")

    def mount_storage(self):
        """
        Idempotently mounts local physical storage, configures local NFS exports,
        and builds AutoFS Direct client maps to mount all remote cluster SSDs dynamically.
        """
        from lib import metaclaw
        all_devices = metaclaw.Inst.devices()

        # ======================================================================
        # PHASE 0: DEPENDENCY INJECTION
        # ======================================================================
        if platform.system() == 'Linux':
            missing_pkgs = []
            if not shutil.which("exportfs"):
                missing_pkgs.append("nfs-kernel-server")
            if not shutil.which("automount"):
                missing_pkgs.append("autofs")
                missing_pkgs.append("nfs-common")

            if missing_pkgs:
                print(f"Installing missing storage dependencies: {' '.join(missing_pkgs)}...")
                try:
                    env = os.environ.copy()
                    env["DEBIAN_FRONTEND"] = "noninteractive"
                    subprocess.run(['sudo', '-E', 'apt-get', 'update'], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(['sudo', '-E', 'apt-get', 'install', '-y'] + missing_pkgs, env=env, check=True)
                except Exception as e:
                    print(f"DIAGNOSTIC: Failed to install dependencies. NFS/AutoFS might fail: {e}")

        subprocess.run(['sudo', 'mkdir', '-p', '/mnt/cluster/ext'], check=False)

        # ======================================================================
        # PHASE 1: LOCAL PHYSICAL MOUNTS
        # ======================================================================
        local_mounts = []
        attached_uuids = set()

        try:
            res = subprocess.run(['lsblk', '-J', '-o', 'UUID'], capture_output=True, text=True)
            if res.returncode == 0:
                lsblk_data = json.loads(res.stdout)
                def extract_uuids(blocks):
                    for b in blocks:
                        if b.get('uuid'):
                            attached_uuids.add(b['uuid'].upper())
                            attached_uuids.add(b['uuid'].lower())
                        if 'children' in b:
                            extract_uuids(b['children'])
                extract_uuids(lsblk_data.get('blockdevices', []))
        except Exception:
            pass

        # Load internal mounts natively assigned to this node's profile
        local_mounts.extend(self.data.get("mounts", []))

        # Search the global registry for ExternalSSDs physically attached to this node right now
        for uid, dev in all_devices.items():
            if dev.device_type == 'ssd':
                for m in dev.data.get('mounts', []):
                    uuid = m.get('uuid')
                    mp = m.get('mountpoint')
                    if uuid and mp and (uuid.upper() in attached_uuids or uuid.lower() in attached_uuids):
                        local_mounts.append(m)

        # Execute Local Physical Mounts
        for m in local_mounts:
            mp = m.get("mountpoint")
            uuid = m.get("uuid")
            fstype = m.get("fstype")

            if not mp or not uuid or mp == '/':
                continue

            if not os.path.ismount(mp):
                subprocess.run(['sudo', 'mkdir', '-p', mp], check=False)
                cmd = ['sudo', 'mount']
                if fstype:
                    cmd.extend(['-t', fstype])
                cmd.extend([f"UUID={uuid}", mp])
                try:
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print(f"Mounted local physical drive: {uuid} to {mp}")
                except subprocess.CalledProcessError as e:
                    print(f"DIAGNOSTIC: Failed to mount UUID {uuid} to {mp}. Error: {e.stderr.strip()}")

        # ======================================================================
        # PHASE 2: LOCAL NFS EXPORTS (SERVER CONFIGURATION)
        # ======================================================================
        print(f"Configuring NFS Exports for local drives on {self.uid}...")
        exports_lines = []

        # Export the local home directory (/home/metaclaw)
        if self.device_type == 'node' and self.uid != "peridot":
            exports_lines.append("/home/metaclaw 100.64.0.0/10(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)")

        # Export physically attached external SSDs
        for m in local_mounts:
            mp = m.get("mountpoint")
            if mp and mp.startswith("/mnt/cluster/ext/"):
                exports_lines.append(f"{mp} 100.64.0.0/10(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)")

        exports_content = "\n".join(exports_lines) + "\n"
        exports_file = "/tmp/metaclaw.exports"
        with open(exports_file, 'w') as f:
            f.write(exports_content)

        try:
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/exports.d'], check=False)
            subprocess.run(['sudo', 'mv', exports_file, '/etc/exports.d/metaclaw.exports'], check=True)
            if shutil.which("exportfs"):
                res = subprocess.run(['sudo', 'exportfs', '-ra'], capture_output=True, text=True)
                if res.returncode == 0:
                    print("NFS exports reloaded successfully.")
                else:
                    print(f"DIAGNOSTIC: Failed to reload NFS exports: {res.stderr.strip()}")
            else:
                print("DIAGNOSTIC: Skipping exportfs. 'nfs-kernel-server' package is not installed.")
        except Exception as e:
            print(f"DIAGNOSTIC: Failed to configure NFS exports: {e}")

        # ======================================================================
        # PHASE 3: AUTOFS DIRECT CLIENT MAPS (REMOTE DISCOVERY)
        # ======================================================================
        print(f"Configuring AutoFS Direct Maps for cluster storage mesh on {self.uid}...")
        autofs_map_lines = []

        for uid, dev in all_devices.items():
            # Remote Node Home Directories -> /mnt/cluster/<hostname>/home/metaclaw
            if dev.device_type == 'node' and uid != self.uid and uid != "peridot":
                ip = dev.data.get('tailscale_ip')
                if ip:
                    autofs_map_lines.append(f"/mnt/cluster/{uid}/home/metaclaw -fstype=nfs4,rw,soft,intr,timeo=14,retry=2 {ip}:/home/metaclaw")

            # Remote External SSDs -> /mnt/cluster/ext/<ssd_name>
            elif dev.device_type == 'ssd':
                current_host = dev.data.get('current_host')
                if current_host and current_host != self.uid:
                    host_dev = all_devices.get(current_host)
                    if host_dev:
                        ip = host_dev.data.get('tailscale_ip')
                        for m in dev.data.get('mounts', []):
                            mp = m.get('mountpoint')
                            if ip and mp and mp.startswith("/mnt/cluster/ext/"):
                                autofs_map_lines.append(f"{mp} -fstype=nfs4,rw,soft,intr,timeo=14,retry=2 {ip}:{mp}")

        # Local Node Home Directory Symlink (Ensures absolute local consistency)
        try:
            base_dir = f"/mnt/cluster/{self.uid}/home"
            subprocess.run(['sudo', 'mkdir', '-p', base_dir], check=False)
            symlink_target = f"{base_dir}/metaclaw"
            if not os.path.exists(symlink_target) and not os.path.islink(symlink_target):
                subprocess.run(['sudo', 'ln', '-s', '/home/metaclaw', symlink_target], check=True)
        except Exception as e:
            print(f"DIAGNOSTIC: Failed to create local cluster symlink: {e}")

        autofs_content = "\n".join(autofs_map_lines) + "\n"
        autofs_file = "/tmp/auto.metaclaw.direct"
        with open(autofs_file, 'w') as f:
            f.write(autofs_content)

        # Utilizing the AutoFS Direct Mount Syntax (/-)
        master_content = "/- /etc/auto.metaclaw.direct --timeout=0\n"
        master_file = "/tmp/metaclaw.autofs"
        with open(master_file, 'w') as f:
            f.write(master_content)

        try:
            subprocess.run(['sudo', 'mv', autofs_file, '/etc/auto.metaclaw.direct'], check=True)
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/auto.master.d'], check=False)
            subprocess.run(['sudo', 'mv', master_file, '/etc/auto.master.d/metaclaw.autofs'], check=True)

            if shutil.which("systemctl"):
                res = subprocess.run(['sudo', 'systemctl', 'restart', 'autofs'], capture_output=True, text=True)
                if res.returncode == 0:
                    print("AutoFS client service restarted successfully.")
                else:
                    print(f"DIAGNOSTIC: Failed to restart AutoFS: {res.stderr.strip()}")
            else:
                print("DIAGNOSTIC: Skipping AutoFS restart. 'autofs' service not detected.")
        except Exception as e:
            print(f"DIAGNOSTIC: Failed to configure AutoFS: {e}")

class PowerStrip(Device):
    """
    Represents a smart power strip (e.g., Kasa HS300) capable of energy monitoring.
    """
    def get_mac_address(self):
        return self.data.get("mac_address")

    def get_plugs(self):
        return self.data.get("plugs", {})
