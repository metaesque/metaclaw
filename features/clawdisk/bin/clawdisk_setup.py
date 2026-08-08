#!/usr/bin/env python3
"""
ClawDisk Setup
Configures local mounts, NFS exports, and AutoFS mesh maps for distributed storage.
Operates as a modular MetaClaw Feature to prevent God-Object bloat in lib.devices.
"""
import os
import sys
import json
import socket
import subprocess
import platform
import shutil

# Inject lib path dynamically to ensure safe execution
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
lib_dir = os.path.join(repo_root, "lib")
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

import devices

def setup_clawdisk(my_uid):
    all_devices = devices.get_all_devices()
    my_device = None

    for uid, dev in all_devices.items():
        if my_uid.lower() in [uid.lower(), dev.name.lower()]:
            my_device = dev
            break

    if not my_device or my_device.device_type != 'node':
        print(f"Device '{my_uid}' is not a registered compute node. Skipping ClawDisk setup.")
        return

    my_dac_ip = my_device.data.get('dac_ip')

    # ======================================================================
    # PHASE 0: DEPENDENCY INJECTION & KERNEL LOCK RELEASE
    # ======================================================================
    if platform.system() == 'Linux':
        missing_pkgs = []
        if not shutil.which("exportfs"):
            missing_pkgs.append("nfs-kernel-server")
        if not shutil.which("automount"):
            missing_pkgs.append("autofs")
            missing_pkgs.append("nfs-common")
        if not shutil.which("mount.exfat-fuse"):
            missing_pkgs.append("exfat-fuse")

        if missing_pkgs:
            print(f"Installing missing storage dependencies: {' '.join(missing_pkgs)}...")
            try:
                env = os.environ.copy()
                env["DEBIAN_FRONTEND"] = "noninteractive"
                subprocess.run(['sudo', '-E', 'apt-get', 'update'], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', '-E', 'apt-get', 'install', '-y'] + missing_pkgs, env=env, check=True)
            except Exception as e:
                print(f"DIAGNOSTIC: Failed to install dependencies. NFS/AutoFS might fail: {e}")

        # Stop autofs immediately. If an old indirect map is active on /mnt/cluster,
        # it prevents root from executing mkdir. Stopping it releases the kernel lock.
        subprocess.run(['sudo', 'systemctl', 'stop', 'autofs'], check=False, stderr=subprocess.DEVNULL)

        # Stop nfs-kernel-server to release any active export locks on block devices
        # This is critical to allow exFAT remounting to function properly in Phase 1
        subprocess.run(['sudo', 'systemctl', 'stop', 'nfs-kernel-server'], check=False, stderr=subprocess.DEVNULL)

    # Cleanup legacy symlink from early iterations if it exists
    legacy_symlink = f"/mnt/cluster/{my_device.uid}"
    if os.path.islink(legacy_symlink):
        subprocess.run(['sudo', 'rm', '-f', legacy_symlink], check=False)

    subprocess.run(['sudo', 'mkdir', '-p', '/mnt/cluster/ext'], check=False)

    # ======================================================================
    # PHASE 0.5: DAC NETWORK INTERFACE CONFIGURATION
    # ======================================================================
    if my_dac_ip and platform.system() == 'Linux':
        best_iface = None
        try:
            for iface in os.listdir('/sys/class/net/'):
                if iface in ['lo'] or iface.startswith('docker') or iface.startswith('veth') or iface.startswith('tailscale') or iface.startswith('br-'):
                    continue

                vendor_path = f'/sys/class/net/{iface}/device/vendor'
                speed_path = f'/sys/class/net/{iface}/speed'

                if os.path.exists(vendor_path):
                    with open(vendor_path, 'r') as f:
                        if f.read().strip() == '0x15b3':
                            best_iface = iface
                            break

                if os.path.exists(speed_path):
                    try:
                        with open(speed_path, 'r') as f:
                            speed_str = f.read().strip()
                            if speed_str.isdigit() and int(speed_str) >= 100000:
                                best_iface = iface
                                break
                    except OSError:
                        pass
        except Exception as e:
            print(f"DIAGNOSTIC: Error searching for DAC network interface: {e}")

        if best_iface:
            check_ip = subprocess.run(['ip', 'addr', 'show', best_iface], capture_output=True, text=True)
            if my_dac_ip not in check_ip.stdout:
                print(f"Assigning persistent DAC IP {my_dac_ip}/24 to high-speed interface {best_iface} via Netplan...")

                if shutil.which("nmcli"):
                    subprocess.run(['sudo', 'nmcli', 'dev', 'set', best_iface, 'managed', 'no'], check=False, stderr=subprocess.DEVNULL)

                netplan_yaml = f"""network:
  version: 2
  ethernets:
    {best_iface}:
      addresses: [{my_dac_ip}/24]
      dhcp4: false
      dhcp6: false
      optional: true
"""
                yaml_path = f"/tmp/99-dac-{best_iface}.yaml"
                with open(yaml_path, 'w') as f:
                    f.write(netplan_yaml)

                try:
                    subprocess.run(['sudo', 'mv', yaml_path, f'/etc/netplan/99-dac-{best_iface}.yaml'], check=True)
                    subprocess.run(['sudo', 'chmod', '600', f'/etc/netplan/99-dac-{best_iface}.yaml'], check=True)
                    subprocess.run(['sudo', 'netplan', 'apply'], check=True)
                    print(f"Netplan applied successfully for {best_iface}.")
                except Exception as e:
                    print(f"DIAGNOSTIC: Failed to apply netplan configuration: {e}")
        else:
            print(f"DIAGNOSTIC: Could not auto-detect a 100Gbps+ or Mellanox network interface for DAC IP {my_dac_ip}.")

    # ======================================================================
    # PHASE 1: LOCAL PHYSICAL MOUNTS & PERMISSIONS
    # ======================================================================
    local_mounts = []
    attached_uuids = set()
    uuid_to_dev = {}

    try:
        res = subprocess.run(['lsblk', '-J', '-o', 'NAME,UUID'], capture_output=True, text=True)
        if res.returncode == 0:
            lsblk_data = json.loads(res.stdout)
            def extract_uuids(blocks):
                for b in blocks:
                    if b.get('uuid'):
                        attached_uuids.add(b['uuid'].upper())
                        attached_uuids.add(b['uuid'].lower())
                        uuid_to_dev[b['uuid'].upper()] = f"/dev/{b.get('name')}"
                    if 'children' in b:
                        extract_uuids(b['children'])
            extract_uuids(lsblk_data.get('blockdevices', []))
    except Exception:
        pass

    # Load internal mounts natively assigned to this node's profile
    local_mounts.extend(my_device.data.get("mounts", []))

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

        is_mounted = os.path.ismount(mp)

        # Fix for exFAT permission dropping: If mounted without uid=1000, unmount it to force a clean mount.
        # The Linux in-kernel exfat driver ignores uid/gid changes during a standard 'remount'.
        # Since nfs-kernel-server is stopped, standard umount (no -l) will cleanly release the device.
        if is_mounted and fstype in ['exfat', 'vfat', 'ntfs', 'fat32']:
            check_mount = subprocess.run(['mount'], capture_output=True, text=True)
            for line in check_mount.stdout.split('\n'):
                if f"on {mp} type" in line and 'uid=1000' not in line:
                    print(f"DIAGNOSTIC: {mp} is mounted without uid=1000 ownership. Unmounting for clean remount...")
                    subprocess.run(['sudo', 'umount', mp], check=False)
                    is_mounted = False
                    break

        if not is_mounted:
            # Ensure placeholder directory is created and owned by metaclaw before mounting
            subprocess.run(['sudo', 'mkdir', '-p', mp], check=False)
            subprocess.run(['sudo', 'chown', '1000:1000', mp], check=False)
            subprocess.run(['sudo', 'chmod', '0777', mp], check=False)

            dev_path = uuid_to_dev.get(uuid.upper())
            if not dev_path:
                try:
                    res_bl = subprocess.run(['blkid', '-U', uuid], capture_output=True, text=True, check=True)
                    dev_path = res_bl.stdout.strip()
                except Exception:
                    dev_path = f"UUID={uuid}"

            # Deploy FUSE bypass to ensure NFS export compatibility for exFAT
            if fstype == 'exfat':
                cmd = ['sudo', 'mount.exfat-fuse', '-o', 'rw,uid=1000,gid=1000,dmask=0000,fmask=0000', dev_path, mp]
            else:
                cmd = ['sudo', 'mount']
                if fstype:
                    cmd.extend(['-t', fstype])

                # Force vfat/fat32/ntfs to recognize UID 1000 and grant 0777 permissions
                if fstype in ['vfat', 'ntfs', 'fat32']:
                    cmd.extend(['-o', 'rw,uid=1000,gid=1000,dmask=0000,fmask=0000'])

                cmd.extend([f"UUID={uuid}", mp])

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"Mounted local physical drive: {uuid} to {mp}")

                # For some file systems, the chown command must be executed on the mount point POST-mount
                if fstype not in ['exfat', 'vfat', 'ntfs', 'fat32']:
                    subprocess.run(['sudo', 'chown', '-R', '1000:1000', mp], check=False)
                    subprocess.run(['sudo', 'chmod', '-R', '0777', mp], check=False)

            except subprocess.CalledProcessError as e:
                print(f"DIAGNOSTIC: Failed to mount UUID {uuid} to {mp}. Error: {e.stderr.strip()}")

    # ======================================================================
    # PHASE 2: LOCAL NFS EXPORTS (SERVER CONFIGURATION)
    # ======================================================================
    print(f"Configuring NFS Exports for local drives on {my_device.uid}...")
    exports_lines = []
    fsid_counter = 1

    # Export the local home directory (/home/metaclaw)
    if my_device.uid != "peridot":
        exports_lines.append(f"/home/metaclaw 100.64.0.0/10(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000,fsid={fsid_counter})")
        if my_dac_ip:
            # Assuming standard /24 subnet for Point-to-Point DAC routes
            exports_lines.append(f"/home/metaclaw 10.99.0.0/24(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000,fsid={fsid_counter})")
        fsid_counter += 1

    # Only export physically attached external SSDs
    for m in local_mounts:
        mp = m.get("mountpoint")
        if mp and mp.startswith("/mnt/cluster/ext/"):
            exports_lines.append(f"{mp} 100.64.0.0/10(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000,fsid={fsid_counter})")
            if my_dac_ip:
                exports_lines.append(f"{mp} 10.99.0.0/24(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000,fsid={fsid_counter})")
            fsid_counter += 1

    exports_content = "\n".join(exports_lines) + "\n"
    exports_file = "/tmp/metaclaw.exports"
    with open(exports_file, 'w') as f:
        f.write(exports_content)

    try:
        subprocess.run(['sudo', 'mkdir', '-p', '/etc/exports.d'], check=False)
        subprocess.run(['sudo', 'mv', exports_file, '/etc/exports.d/metaclaw.exports'], check=True)

        # Start nfs-kernel-server back up if it was stopped in Phase 0
        if shutil.which("systemctl"):
            subprocess.run(['sudo', 'systemctl', 'start', 'nfs-kernel-server'], check=False, stderr=subprocess.DEVNULL)

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
    # PHASE 3: AUTOFS DIRECT CLIENT MAPS (NFS FAILOVER MESH)
    # ======================================================================
    print(f"Configuring AutoFS Direct Maps for cluster storage mesh on {my_device.uid}...")
    autofs_map_lines = []

    # Extract dynamic Tailscale IPs directly from profile.json
    profile_path = os.path.join(repo_root, "profile.json")
    profile_ips = {}
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                prof_data = json.load(f)
                for n in prof_data.get('nodes', []):
                    hostname = n.get('hostname', '')
                    ip = n.get('hardware', {}).get('ip_address')
                    if hostname and ip:
                        profile_ips[hostname.lower()] = ip
        except Exception as e:
            print(f"DIAGNOSTIC: Failed to parse profile.json for IPs: {e}")

    all_nodes = [d for d in all_devices.values() if d.device_type == 'node']

    for uid, dev in all_devices.items():
        # Remote Node Home Directories
        if dev.device_type == 'node' and uid != my_device.uid and uid != "peridot":
            target_ip = profile_ips.get(uid.lower())
            target_dac_ip = dev.data.get('dac_ip')

            if my_dac_ip and target_dac_ip:
                target_ip = target_dac_ip

            if target_ip:
                remote_home_mp = f"/mnt/cluster/{uid}/home/metaclaw"
                subprocess.run(['sudo', 'mkdir', '-p', remote_home_mp], check=False)
                subprocess.run(['sudo', 'chown', '1000:1000', remote_home_mp], check=False)
                # Removed deprecated 'intr' flag
                autofs_map_lines.append(f"{remote_home_mp} -fstype=nfs4,rw,soft,timeo=14,retry=2 {target_ip}:/home/metaclaw")

        # External SSDs (NFS Replicated Server Failover)
        elif dev.device_type == 'ssd':
            # FIX 1: Prevent AutoFS from hijacking physically attached local drives
            is_physically_attached = False
            for m in dev.data.get('mounts', []):
                uuid = m.get('uuid')
                if uuid and (uuid.upper() in attached_uuids or uuid.lower() in attached_uuids):
                    is_physically_attached = True
                    break

            if is_physically_attached:
                continue

            for m in dev.data.get('mounts', []):
                mp = m.get('mountpoint')
                if mp and mp.startswith("/mnt/cluster/ext/"):
                    # Ensure the placeholder directory is visible locally even when not mounted
                    subprocess.run(['sudo', 'mkdir', '-p', mp], check=False)
                    subprocess.run(['sudo', 'chown', '1000:1000', mp], check=False)

                    locations = []
                    for node in all_nodes:
                        if node.uid == my_device.uid:
                            continue  # Do not loopback mount from ourselves

                        # FIX 2: Use profile.json dictionary to extract Tailscale IPs
                        n_ip = profile_ips.get(node.uid.lower())
                        n_dac = node.data.get('dac_ip')
                        if my_dac_ip and n_dac:
                            n_ip = n_dac

                        if n_ip:
                            locations.append(n_ip)

                    if locations:
                        # FIX 3: Replicated Server Comma Syntax
                        loc_str = ",".join(locations) + ":" + mp
                        autofs_map_lines.append(f"{mp} -fstype=nfs4,rw,soft,timeo=14,retry=2 {loc_str}")

    # Local Node Home Directory Symlink (Ensures absolute local consistency)
    try:
        base_dir = f"/mnt/cluster/{my_device.uid}/home"
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

if __name__ == "__main__":
    node_uid = sys.argv[1] if len(sys.argv) > 1 else socket.gethostname().lower()
    setup_clawdisk(node_uid)
