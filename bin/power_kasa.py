# Implemented in https://gemini.google.com/u/1/app/b0ca4e11115f2fe1
import asyncio
import os
import sqlite3
import argparse
import re
import subprocess
import warnings
from datetime import datetime, timezone, timedelta
from kasa import Discover, DeviceType, Module

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SEED_DATA = {
    "48:22:54:30:02:D1": { 
        "name": "Main Rack Strip",
        "devices": [
            ("dev_rt", "Shaw Router", "Main ISP Router"),
            ("dev_uk", "Unknown", "Unidentified load"),
            ("dev_em", "Empty", "No physical device connected"),
            ("dev_cp", "compute (EVO-X2)", "Primary compute node"),
            ("dev_ct", "control (K8 Plus)", "Control plane mini-pc"),
            ("dev_sw", "Binardat Switch", "Network switch")
        ]
    }
}

# ==============================================================================
# DATABASE CORE
# ==============================================================================

class PowerDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_schema()

    def _initialize_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strips (
                    mac_address TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    uid TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_mapping (
                    mac_address TEXT NOT NULL,
                    plug_index INTEGER NOT NULL,
                    device_uid TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT,
                    PRIMARY KEY (mac_address, plug_index, valid_from),
                    FOREIGN KEY (device_uid) REFERENCES devices (uid) ON UPDATE CASCADE,
                    FOREIGN KEY (mac_address) REFERENCES strips (mac_address) ON UPDATE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    timestamp TEXT NOT NULL,
                    mac_address TEXT NOT NULL,
                    plug_index INTEGER NOT NULL,
                    watts REAL NOT NULL,
                    volts REAL NOT NULL,
                    amps REAL NOT NULL,
                    PRIMARY KEY (timestamp, mac_address, plug_index)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date TEXT NOT NULL,
                    mac_address TEXT NOT NULL,
                    plug_index INTEGER NOT NULL,
                    kwh REAL NOT NULL,
                    PRIMARY KEY (date, mac_address, plug_index)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp)")

    def execute_read(self, query: str, params: tuple = ()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()

    def execute_write(self, query: str, params: tuple = ()):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute(query, params)

# ==============================================================================
# ENTITY MODELS
# ==============================================================================

class TimeSeries:
    def __init__(self, data: list):
        self._data = data

    def points(self):
        return [(r['timestamp'], r['watts'], r['volts'], r['amps']) for r in self._data]

    def average_watts(self):
        if not self._data:
            return 0.0
        return sum(r['watts'] for r in self._data) / len(self._data)


class Device:
    def __init__(self, db: PowerDB, uid: str):
        self._db = db
        self._uid = uid
        rows = db.execute_read("SELECT name, description FROM devices WHERE uid = ?", (uid,))
        if not rows:
            raise ValueError(f"Device UID '{uid}' does not exist in the database.")
        self._name = rows[0]['name']
        self._description = rows[0]['description']

    def uid(self):
        return self._uid

    def name(self):
        return self._name

    def description(self):
        return self._description

    def timeseries(self, start: str = None, end: str = None) -> TimeSeries:
        query = """
            SELECT t.timestamp, t.watts, t.volts, t.amps
            FROM telemetry t
            JOIN device_mapping m ON t.mac_address = m.mac_address 
                                 AND t.plug_index = m.plug_index
            WHERE m.device_uid = ?
              AND t.timestamp >= m.valid_from
              AND (m.valid_to IS NULL OR t.timestamp < m.valid_to)
        """
        params = [self._uid]

        if start:
            query += " AND t.timestamp >= ?"
            params.append(start)
        if end:
            query += " AND t.timestamp <= ?"
            params.append(end)

        query += " ORDER BY t.timestamp ASC"
        
        data = self._db.execute_read(query, tuple(params))
        return TimeSeries(data)


class Strip:
    def __init__(self, db: PowerDB, mac_address: str):
        self._db = db
        self._mac = mac_address
        rows = db.execute_read("SELECT name, description FROM strips WHERE mac_address = ?", (mac_address,))
        if not rows:
            raise ValueError(f"Strip MAC '{mac_address}' does not exist in the database.")
        self._name = rows[0]['name']
        self._description = rows[0]['description']

    def mac(self):
        return self._mac

    def name(self):
        return self._name


class Env:
    def __init__(self, db: PowerDB):
        self.db = db
        self._devices = {}
        self._strips_by_mac = {}
        self._strips_by_name = {}
        self._strips_by_index = {}
        self.refresh()

    def refresh(self):
        self._devices.clear()
        for row in self.db.execute_read("SELECT uid FROM devices"):
            uid = row['uid']
            self._devices[uid] = Device(self.db, uid)

        self._strips_by_mac.clear()
        self._strips_by_name.clear()
        self._strips_by_index.clear()
        
        rows = self.db.execute_read("SELECT mac_address FROM strips ORDER BY mac_address")
        for idx, row in enumerate(rows, start=1):
            mac = row['mac_address']
            strip = Strip(self.db, mac)
            self._strips_by_mac[mac] = strip
            self._strips_by_name[strip.name()] = strip
            self._strips_by_index[idx] = strip
            self._strips_by_index[str(idx)] = strip

    def get_device(self, identifier: str) -> Device:
        if identifier in self._devices:
            return self._devices[identifier]
        for dev in self._devices.values():
            if dev.name() == identifier:
                return dev
        return None

    def get_strip(self, identifier) -> Strip:
        if identifier in self._strips_by_mac:
            return self._strips_by_mac[identifier]
        if identifier in self._strips_by_name:
            return self._strips_by_name[identifier]
        if identifier in self._strips_by_index:
            return self._strips_by_index[identifier]
        try:
            if int(identifier) in self._strips_by_index:
                return self._strips_by_index[int(identifier)]
        except ValueError:
            pass
        return None

# ==============================================================================
# OPERATIONS
# ==============================================================================

def bootstrap_db(db: PowerDB):
    """Ensures database reflects the SEED_DATA configuration."""
    db.execute_write("INSERT OR IGNORE INTO devices (uid, name, description) VALUES (?, ?, ?)", 
                     ("dev_unmapped", "Unmapped", "Default state"))
    
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for mac, strip_info in SEED_DATA.items():
        db.execute_write("INSERT OR IGNORE INTO strips (mac_address, name, description) VALUES (?, ?, ?)", 
                         (mac, strip_info['name'], "Bootstrapped from seed data"))
        
        for idx, (uid, name, desc) in enumerate(strip_info['devices']):
            db.execute_write("INSERT OR IGNORE INTO devices (uid, name, description) VALUES (?, ?, ?)", 
                             (uid, name, desc))
            
            existing = db.execute_read("""
                SELECT device_uid FROM device_mapping 
                WHERE mac_address = ? AND plug_index = ? AND valid_to IS NULL
            """, (mac, idx))
            
            if not existing:
                db.execute_write("""
                    INSERT INTO device_mapping (mac_address, plug_index, device_uid, valid_from, valid_to) 
                    VALUES (?, ?, ?, ?, NULL)
                """, (mac, idx, uid, current_time))


async def poll_devices(env: Env, target_strip_arg: str = None, fetch_daily: bool = False):
    target_strip = None
    if target_strip_arg:
        target_strip = env.get_strip(target_strip_arg)
        if not target_strip:
            print(f"[!] Warning: Target strip '{target_strip_arg}' does not exist in the environment.")
            print("    Valid strip indices/names/MACs currently tracked:")
            for k, v in env._strips_by_index.items():
                if isinstance(k, int):
                    print(f"      - Index {k}: {v.name()} ({v.mac()})")
            return

    print("Initiating Kasa device poll...\n")
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        found_devices = await Discover.discover(timeout=5)
        if not found_devices:
            print("No Kasa devices found on network.")
            return

        strip_ips = sorted([ip for ip, dev in found_devices.items() if dev.device_type == DeviceType.Strip])
        
        for ip in strip_ips:
            device = found_devices[ip]
            await device.update()
            mac = device.mac

            if mac not in SEED_DATA:
                print(f"[!] Warning: Discovered unconfigured MAC address {mac}.")
                continue

            if target_strip and mac != target_strip.mac():
                continue

            env.db.execute_write("INSERT OR IGNORE INTO strips (mac_address, name, description) VALUES (?, ?, ?)", 
                             (mac, SEED_DATA[mac]['name'], "Auto-discovered strip"))
            env.refresh() 
            resolved_strip = env.get_strip(mac)

            runtime_idx = None
            for k, v in env._strips_by_index.items():
                if isinstance(k, int) and v.mac() == mac:
                    runtime_idx = k
                    break

            print(f"Strip [{runtime_idx}] MAC: {mac} | Time: {current_time}")
            print("-" * 67)
            print(f"{'#':<1} | {'Power':>7} | {'Voltage':>7} | {'Current':>7} | {'Device':<8} | {'Device':<25}")
            print(f"{'':<1} | {'(W)':>7} | {'(V)':>7} | {'(A)':>7} | {'(uid)':<8} | {'(name)':<25}")
            print("-" * 67)

            daily_acquired_data = []

            for idx, plug in enumerate(device.children):
                energy = plug.modules[Module.Energy]
                power = float(getattr(energy, 'current_consumption', getattr(energy, 'power', 0.0)))
                voltage = float(energy.voltage)
                current = float(energy.current)

                env.db.execute_write("""
                    INSERT INTO telemetry (timestamp, mac_address, plug_index, watts, volts, amps) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time, mac, idx, power, voltage, current))

                mapping = env.db.execute_read("""
                    SELECT d.uid, d.name FROM device_mapping m
                    JOIN devices d ON m.device_uid = d.uid
                    WHERE m.mac_address = ? AND m.plug_index = ? AND m.valid_to IS NULL
                """, (mac, idx))
                
                dev_uid = mapping[0]['uid'] if mapping else "dev_unmapped"
                dev_name = mapping[0]['name'] if mapping else "Unmapped"

                print(f"{idx:<1} | {power:>7.3f} | {voltage:>7.3f} | {current:>7.3f} | {dev_uid:<8} | {dev_name:<25}")

                if fetch_daily:
                    try:
                        # Attempt modernized API execution; fallback to warnings suppression
                        try:
                            res = await plug.modules[Module.Energy].get_emeter_daily(year=datetime.now().year, month=datetime.now().month)
                        except AttributeError:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", DeprecationWarning)
                                res = await plug.get_emeter_daily(year=datetime.now().year, month=datetime.now().month)

                        for day, kwh in res.items():
                            date_str = f"{datetime.now().year:04d}-{datetime.now().month:02d}-{int(day):02d}"
                            env.db.execute_write("""
                                REPLACE INTO daily_summary (date, mac_address, plug_index, kwh)
                                VALUES (?, ?, ?, ?)
                            """, (date_str, mac, idx, float(kwh)))

                            daily_acquired_data.append({
                                'date': date_str,
                                'kwh': float(kwh),
                                'uid': dev_uid,
                                'name': dev_name,
                                'plug': idx
                            })
                    except Exception as e:
                        print(f"[!] Failed to acquire daily data for plug {idx}: {e}")

            print("-" * 67 + "\n")

            if fetch_daily and daily_acquired_data:
                print(f"Daily Hardware Statistics Acquired for MAC: {mac}")
                print("-" * 59)
                print(f"{'Day':<10} | {'Energy':>7} | {'Device':<8} | {'Device':<25}")
                print(f"{'':<10} | {'(kWh)':>7} | {'(uid)':<8} | {'(name)':<25}")
                print("-" * 59)
                
                for d in sorted(daily_acquired_data, key=lambda x: (x['date'], x['plug'])):
                    print(f"{d['date']:<10} | {d['kwh']:>7.3f} | {d['uid']:<8} | {d['name']:<25}")
                print("-" * 59 + "\n")

    except Exception as e:
        print(f"Error during polling: {e}")


async def _daemon_loop(env: Env, device, offset: int):
    """Internal loop for a single strip running indefinitely."""
    mac = device.mac
    await asyncio.sleep(offset)
    print(f"[DAEMON] Strip {mac} started with offset {offset}s.")
    
    while True:
        try:
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            await device.update()
            
            for idx, plug in enumerate(device.children):
                energy = plug.modules[Module.Energy]
                power = float(getattr(energy, 'current_consumption', getattr(energy, 'power', 0.0)))
                voltage = float(energy.voltage)
                current = float(energy.current)

                env.db.execute_write("""
                    INSERT INTO telemetry (timestamp, mac_address, plug_index, watts, volts, amps) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time, mac, idx, power, voltage, current))
                
        except Exception as e:
            print(f"[DAEMON] Error polling strip {mac}: {e}")
            
        await asyncio.sleep(15)

async def run_daemon(env: Env):
    """Discovers strips and initializes staggered, infinite polling loops."""
    print("[DAEMON] Initializing Kasa network discovery...")
    try:
        found_devices = await Discover.discover(timeout=5)
    except Exception as e:
        print(f"[DAEMON] Fatal discovery error: {e}")
        return

    strip_ips = sorted([ip for ip, dev in found_devices.items() if dev.device_type == DeviceType.Strip])
    
    if not strip_ips:
        print("[DAEMON] No Kasa strips found. Exiting.")
        return

    tasks = []
    for idx, ip in enumerate(strip_ips):
        device = found_devices[ip]
        mac = device.mac
        
        if mac not in SEED_DATA:
            print(f"[DAEMON] Skipping unconfigured strip: {mac}")
            continue
            
        offset = idx * 5
        tasks.append(asyncio.create_task(_daemon_loop(env, device, offset)))

    print(f"[DAEMON] Discovery complete. {len(tasks)} strips targeted. Entering infinite poll loop.")
    await asyncio.gather(*tasks)


def cli_move(env: Env, uid: str, mac: str, plug: int):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    env.db.execute_write("UPDATE device_mapping SET valid_to = ? WHERE mac_address = ? AND plug_index = ? AND valid_to IS NULL",
                     (current_time, mac, plug))
    
    env.db.execute_write("UPDATE device_mapping SET valid_to = ? WHERE device_uid = ? AND valid_to IS NULL",
                     (current_time, uid))
                     
    env.db.execute_write("INSERT INTO device_mapping (mac_address, plug_index, device_uid, valid_from, valid_to) VALUES (?, ?, ?, ?, NULL)",
                     (mac, plug, uid, current_time))
    print(f"Device {uid} mapped to Strip {mac} Plug {plug} at {current_time}.")


def cli_rename(env: Env, uid: str, new_name: str, desc: str = None):
    if desc:
        env.db.execute_write("UPDATE devices SET name = ?, description = ? WHERE uid = ?", (new_name, desc, uid))
    else:
        env.db.execute_write("UPDATE devices SET name = ? WHERE uid = ?", (new_name, uid))
    print(f"Device {uid} renamed to '{new_name}'.")


def cli_query(env: Env, start_str: str, end_str: str, device_filter: str, strip_filter: str):
    def parse_dt(d_str: str) -> datetime:
        formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
        for fmt in formats:
            try:
                return datetime.strptime(d_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        raise ValueError(f"Date string '{d_str}' does not match expected formats: YYYY-mm-dd, YYYY-mm-dd HH:MM, YYYY-mm-dd HH:MM:SS")

    now = datetime.now(timezone.utc)
    
    start_dt = parse_dt(start_str) if start_str else (now - timedelta(days=7))
    end_dt = parse_dt(end_str) if end_str else now

    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    device_re = re.compile(device_filter) if device_filter else None
    strip_re = re.compile(strip_filter) if strip_filter else None

    query = """
        SELECT t.timestamp, t.watts, t.volts, t.amps, 
               COALESCE(d.name, 'Unmapped') as device_name, 
               s.name as strip_name
        FROM telemetry t
        JOIN strips s ON t.mac_address = s.mac_address
        LEFT JOIN device_mapping m ON t.mac_address = m.mac_address 
                                  AND t.plug_index = m.plug_index
                                  AND t.timestamp >= m.valid_from 
                                  AND (m.valid_to IS NULL OR t.timestamp < m.valid_to)
        LEFT JOIN devices d ON m.device_uid = d.uid
        WHERE t.timestamp >= ? AND t.timestamp <= ?
        ORDER BY t.timestamp ASC, t.mac_address ASC, t.plug_index ASC
    """
    
    rows = env.db.execute_read(query, (start_iso, end_iso))
    
    print(f"Query Range (UTC limits): {start_iso} to {end_iso}")
    print("-" * 97)
    print(f"{'Date':<19} | {'Power':>7} | {'Voltage':>7} | {'Current':>7} | {'Device':<25} | {'Strip':<20}")
    print(f"{'':<19} | {'(W)':>7} | {'(V)':>7} | {'(A)':>7} | {'(name)':<25} | {'(name)':<20}")
    print("-" * 97)
    
    displayed_count = 0
    for r in rows:
        dev_name = r['device_name']
        strip_name = r['strip_name']

        if device_re and not device_re.search(dev_name):
            continue
        if strip_re and not strip_re.search(strip_name):
            continue
            
        dt_utc = datetime.strptime(r['timestamp'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone()
        dt_str = dt_local.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"{dt_str:<19} | {r['watts']:>7.3f} | {r['volts']:>7.3f} | {r['amps']:>7.3f} | {dev_name:<25} | {strip_name:<20}")
        displayed_count += 1
    
    print("-" * 97)
    print(f"Total records retrieved: {len(rows)} (Displayed: {displayed_count})\n")


def cli_backup(env: Env, target_path: str, bucket_name: str):
    print("Initiating database backup...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = os.path.basename(env.db.db_path)
    tmp_backup_path = f"/tmp/{db_filename}.{timestamp}.bak"

    try:
        with sqlite3.connect(env.db.db_path) as src, sqlite3.connect(tmp_backup_path) as dst:
            src.backup(dst)
        print(f"[+] Local snapshot created at {tmp_backup_path}")
    except Exception as e:
        print(f"[!] Failed to snapshot database: {e}")
        return

    if not os.path.exists(target_path):
        print(f"[!] Target path '{target_path}' does not exist. Attempting creation...")
        try:
            os.makedirs(target_path, exist_ok=True)
        except Exception as e:
            print(f"[!] Failed to create target path: {e}")
            os.remove(tmp_backup_path)
            return

    print(f"[*] Rsyncing snapshot to {target_path}...")
    try:
        subprocess.run(['rsync', '-a', tmp_backup_path, target_path], check=True)
        print(f"[+] Rsync complete.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Rsync failed: {e}")

    if bucket_name:
        try:
            from google.cloud import storage
            print(f"[*] Uploading snapshot to Google Cloud Storage bucket '{bucket_name}'...")
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            destination_blob_name = os.path.basename(tmp_backup_path)
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_filename(tmp_backup_path)
            print(f"[+] GCP upload complete: gs://{bucket_name}/{destination_blob_name}")
        except ImportError:
            print("[!] GCP Upload skipped: 'google-cloud-storage' library is not installed.")
        except Exception as e:
            print(f"[!] GCP Upload failed: {e}")
            
    try:
        os.remove(tmp_backup_path)
    except OSError:
        pass
    print("Backup sequence finished.")

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(script_dir, "data", "metaclaw_power.db")
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    db = PowerDB(db_file)
    bootstrap_db(db)
    
    env = Env(db)

    parser = argparse.ArgumentParser(description="Kasa Power Discovery and Telemetry via SQLite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: daemon
    parser_daemon = subparsers.add_parser('daemon', help="Run continuous polling daemon (for systemd)")

    # Subcommand: poll
    parser_poll = subparsers.add_parser('poll', help="Poll network for Kasa strips and log telemetry")
    parser_poll.add_argument('-s', '--strip', type=str, default=None, help="Specific strip index, name, or MAC to poll. Defaults to all.")
    parser_poll.add_argument('-d', '--daily', action='store_true', help="Fetch and log daily kWh aggregates.")

    # Subcommand: move
    parser_move = subparsers.add_parser('move', help="Map a device to a specific physical strip and plug")
    parser_move.add_argument('uid', type=str, help="Device UID")
    parser_move.add_argument('mac', type=str, help="Strip MAC Address")
    parser_move.add_argument('plug', type=int, help="Plug Index (0-5)")

    # Subcommand: rename
    parser_rename = subparsers.add_parser('rename', help="Rename a device")
    parser_rename.add_argument('uid', type=str, help="Device UID")
    parser_rename.add_argument('name', type=str, help="New Human-Readable Name")
    parser_rename.add_argument('--desc', type=str, help="New Description", default=None)

    # Subcommand: query
    parser_query = subparsers.add_parser('query', help="Query telemetry data for a given date range")
    parser_query.add_argument('-b', '--start', type=str, default="", help="Start date (YYYY-mm-dd [HH:MM[:SS]])")
    parser_query.add_argument('-e', '--end', type=str, default="", help="End date (YYYY-mm-dd [HH:MM[:SS]])")
    parser_query.add_argument('-d', '--device', type=str, default="", help="Regex filter for Device name")
    parser_query.add_argument('-s', '--strip', type=str, default="", help="Regex filter for Strip name")

    # Subcommand: backup
    parser_backup = subparsers.add_parser('backup', help="Safe snapshot and backup of SQLite database")
    parser_backup.add_argument('--path', type=str, required=True, help="Local directory path to rsync backup file to")
    parser_backup.add_argument('--bucket', type=str, default=None, help="GCP Bucket name for cloud storage upload")

    args = parser.parse_args()

    if args.command == 'daemon':
        asyncio.run(run_daemon(env))
    elif args.command == 'poll':
        asyncio.run(poll_devices(env, args.strip, args.daily))
    elif args.command == 'move':
        cli_move(env, args.uid, args.mac, args.plug)
    elif args.command == 'rename':
        cli_rename(env, args.uid, args.name, args.desc)
    elif args.command == 'query':
        cli_query(env, args.start, args.end, args.device, args.strip)
    elif args.command == 'backup':
        cli_backup(env, args.path, args.bucket)
