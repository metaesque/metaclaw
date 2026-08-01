# Implemented in https://gemini.google.com/u/1/app/b0ca4e11115f2fe1
import asyncio
import os
import sqlite3
import argparse
import re
import subprocess
import contextlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from kasa import Discover, DeviceType, Module

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SEED_DATA = {
    "48:22:54:30:02:D1": {
        "name": "Main Rack Strip",
        "devices": [
            ("router", "Shaw Router", "Main ISP Router"),
            ("solar", "Solar ECU", "APsystems Energy Control Unit"),
            ("empty", "Empty", "No physical device connected"),
            ("compute", "GMKtec EVO-X2", "Primary compute node"),
            ("control", "GMKtec K8 Plus", "Control plane mini-pc"),
            ("switch", "Binardat Switch", "Network switch")
        ]
    }
}

# ==============================================================================
# UTILITIES
# ==============================================================================

def format_utc_to_local(iso_str: str) -> str:
    """Converts a UTC ISO 8601 string to local YYYY-mm-dd HH:MM:SS."""
    if not iso_str or iso_str == "NULL":
        return "NULL"
    try:
        dt_utc = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso_str

def parse_local_to_utc_iso(d_str: str) -> str:
    """Parses a local time string and returns a UTC ISO 8601 string."""
    if not d_str or d_str.lower() == 'now':
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
    formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    local_tz = datetime.now().astimezone().tzinfo
    for fmt in formats:
        try:
            dt_naive = datetime.strptime(d_str, fmt)
            dt_local = dt_naive.replace(tzinfo=local_tz)
            return dt_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
    raise ValueError(f"Date string '{d_str}' does not match expected formats (YYYY-mm-dd HH:MM:SS)")

def printTable(header, rows, indent=""):
    """
    Dynamically sizes and prints tabular data.
    If 'width' is missing or 0, it dynamically bounds to the max data width.
    Header text that exceeds computed width is truncated with a '$'.
    """
    widths = []
    for i, col in enumerate(header):
        w = col.get('width', 0)
        if w == 0:
            if rows:
                w = max(len(str(r[i])) for r in rows)
            else:
                w = len(str(col.get('primary', '')))
        w = max(w, 1)
        widths.append(w)

    def trunc_header(text, w):
        s = str(text) if text is not None else ""
        if len(s) > w:
            return s[:w-1] + '$' if w > 0 else ''
        return s

    def fmt(text, w, align):
        s = str(text) if text is not None else ""
        if align == 'right': return s.rjust(w)
        elif align == 'center': return s.center(w)
        else: return s.ljust(w)

    has_secondary = any(c.get('secondary') for c in header)
    
    p_cells = []
    s_cells = []
    
    for i, col in enumerate(header):
        w = widths[i]
        align = col.get('align', 'left')
        
        p_text = trunc_header(col.get('primary', ''), w)
        p_cells.append(fmt(p_text, w, align))
        
        if has_secondary:
            s_text = trunc_header(col.get('secondary', ''), w)
            s_cells.append(fmt(s_text, w, align))

    p_line = " | ".join(p_cells)
    print(indent + p_line)
    if has_secondary:
        print(indent + " | ".join(s_cells))
    
    print(indent + "-" * len(p_line))
    
    for r in rows:
        r_cells = []
        for i, col in enumerate(header):
            w = widths[i]
            align = col.get('align', 'left')
            r_cells.append(fmt(r[i], w, align))
        print(indent + " | ".join(r_cells))
        
    print(indent + "-" * len(p_line))

# ==============================================================================
# DATABASE TABLES & ENTITY MODELS
# ==============================================================================

class Table(ABC):
    def __init__(self, db: 'PowerDB', schema: str):
        self.db = db
        self.schema = schema

    @abstractmethod
    def summary(self):
        pass


class StripTable(Table):
    def insert(self, mac_address: str, number: int, name: str, description: str):
        self.db.execute_write("INSERT OR IGNORE INTO strips (mac_address, number, name, description) VALUES (?, ?, ?, ?)", 
                         (mac_address, number, name, description))
        self.db.execute_write("UPDATE strips SET number=?, name=?, description=? WHERE mac_address=?", 
                         (number, name, description, mac_address))

    def get_all(self):
        return self.db.execute_read("SELECT * FROM strips ORDER BY number ASC")
        
    def summary(self):
        print("\n# Strips Table\n")
        rows = [[str(r['number']), r['mac_address'], r['name'], r['description']] for r in self.get_all()]
        header = [
            {'primary': '#'},
            {'primary': 'MAC Address'},
            {'primary': 'Name'},
            {'primary': 'Description'}
        ]
        printTable(header, rows, indent="  ")


class DeviceTable(Table):
    def insert(self, uid: str, name: str, description: str):
        self.db.execute_write("INSERT OR IGNORE INTO devices (uid, name, description) VALUES (?, ?, ?)", 
                         (uid, name, description))
                         
    def update(self, uid: str, name: str, description: str):
        self.db.execute_write("UPDATE devices SET name=?, description=? WHERE uid=?", (name, description, uid))

    def get_all(self):
        return self.db.execute_read("SELECT * FROM devices")

    def summary(self):
        print("\n# Devices Table\n")
        rows = [[r['uid'], r['name'], r['description']] for r in self.get_all()]
        header = [
            {'primary': 'UID'},
            {'primary': 'Name'},
            {'primary': 'Description'}
        ]
        printTable(header, rows, indent="  ")


class DeviceMappingTable(Table):
    def map_device(self, mac: str, plug: int, uid: str, timestamp: str):
        existing_target = self.get_active(mac, plug)
        
        if existing_target and existing_target['device_uid'] == uid:
            return  # Already properly mapped here
            
        # Close out the target plug if it currently has a different device
        if existing_target:
            self.db.execute_write("UPDATE device_mapping SET valid_to = ? WHERE mac_address = ? AND plug_index = ? AND valid_to IS NULL", (timestamp, mac, plug))
            
        # Close out the device's old location, and fill that vacated plug with 'empty'
        if uid != 'empty':
            existing_source = self.db.execute_read("SELECT * FROM device_mapping WHERE device_uid = ? AND valid_to IS NULL", (uid,))
            for row in existing_source:
                old_mac = row['mac_address']
                old_plug = row['plug_index']
                self.db.execute_write("UPDATE device_mapping SET valid_to = ? WHERE mac_address = ? AND plug_index = ? AND valid_to IS NULL", (timestamp, old_mac, old_plug))
                self.db.execute_write("INSERT INTO device_mapping (mac_address, plug_index, device_uid, valid_from, valid_to) VALUES (?, ?, 'empty', ?, NULL)", (old_mac, old_plug, timestamp))

        # Map the requested device to the target plug
        self.db.execute_write("INSERT INTO device_mapping (mac_address, plug_index, device_uid, valid_from, valid_to) VALUES (?, ?, ?, ?, NULL)", (mac, plug, uid, timestamp))

    def get_active(self, mac: str, plug: int):
        rows = self.db.execute_read("SELECT * FROM device_mapping WHERE mac_address = ? AND plug_index = ? AND valid_to IS NULL", (mac, plug))
        return rows[0] if rows else None

    def get_all(self):
        return self.db.execute_read("SELECT * FROM device_mapping ORDER BY mac_address, plug_index, valid_from")

    def summary(self):
        print("\n# Device Mapping Table\n")
        
        query = """
            SELECT m.mac_address, s.number as strip_num, m.plug_index, m.device_uid, m.valid_from, m.valid_to
            FROM device_mapping m
            LEFT JOIN strips s ON m.mac_address = s.mac_address
            ORDER BY m.mac_address, m.plug_index, m.valid_from
        """
        raw_rows = self.db.execute_read(query)
        
        rows = []
        for r in raw_rows:
            v_from = format_utc_to_local(r['valid_from'])
            v_to = format_utc_to_local(r['valid_to'])
            s_num = str(r['strip_num']) if r['strip_num'] else "?"
            rows.append([r['mac_address'], s_num, str(r['plug_index']), r['device_uid'], v_from, v_to])
            
        header = [
            {'primary': 'Strip', 'secondary': 'MAC'},
            {'primary': 'Strip', 'secondary': '#'},
            {'primary': 'P', 'align': 'right'},
            {'primary': 'Device', 'secondary': '(uid)'},
            {'primary': 'Valid From', 'width': 20},
            {'primary': 'Valid To', 'width': 20}
        ]
        printTable(header, rows, indent="  ")


class TelemetryTable(Table):
    def insert(self, timestamp: str, mac: str, plug: int, watts: float, volts: float, amps: float):
        self.db.execute_write("""
            INSERT INTO telemetry (timestamp, mac_address, plug_index, watts, volts, amps) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, mac, plug, watts, volts, amps))

    def get_range(self, start_iso: str, end_iso: str):
        query = """
            SELECT t.timestamp, t.watts, t.volts, t.amps, 
                   COALESCE(d.uid, 'empty') as device_uid, 
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
        return self.db.execute_read(query, (start_iso, end_iso))

    def summary(self):
        print("\n# Telemetry Summary Table\n")
        tel_summary = self.db.execute_read("""
            SELECT mac_address, plug_index, COUNT(*) as cnt 
            FROM telemetry 
            GROUP BY mac_address, plug_index 
            ORDER BY mac_address, plug_index
        """)
        rows = [[r['mac_address'], str(r['plug_index']), str(r['cnt'])] for r in tel_summary]
        header = [
            {'primary': 'MAC Address'},
            {'primary': 'P', 'align': 'right'},
            {'primary': '#', 'align': 'right'}
        ]
        printTable(header, rows, indent="  ")


class DailyTable(Table):
    def upsert(self, date_str: str, mac: str, plug: int, kwh: float):
        self.db.execute_write("""
            REPLACE INTO daily (date, mac_address, plug_index, kwh)
            VALUES (?, ?, ?, ?)
        """, (date_str, mac, plug, kwh))

    def get_all_macs(self):
        return [r['mac_address'] for r in self.db.execute_read("SELECT DISTINCT mac_address FROM daily ORDER BY mac_address")]
        
    def get_by_mac(self, mac: str):
        return self.db.execute_read("SELECT date, plug_index, kwh FROM daily WHERE mac_address = ? ORDER BY date, plug_index", (mac,))

    def get_active_uids(self, mac: str):
        plug_uids = []
        for i in range(6):
            m = self.db.execute_read("""
                SELECT d.uid FROM device_mapping m 
                JOIN devices d ON m.device_uid = d.uid 
                WHERE m.mac_address = ? AND m.plug_index = ? AND m.valid_to IS NULL
            """, (mac, i))
            plug_uids.append(m[0]['uid'] if m else f"plug_{i}")
        return plug_uids

    def print_daily_matrix(self, mac: str, cost_table: 'CostTable', indent=""):
        plug_uids = self.get_active_uids(mac)
        data = self.get_by_mac(mac)
        
        if not data:
            return

        matrix = {}
        for r in data:
            d = r['date']
            if d not in matrix:
                matrix[d] = [0.0] * 6
            matrix[d][r['plug_index']] = float(r['kwh'])

        header = [
            {'primary': 'Date'},
            {'primary': '$', 'align': 'right'},
            {'primary': 'kWh', 'width': 7, 'align': 'right'}
        ]
        for uid in plug_uids:
            header.append({'primary': uid, 'width': 7, 'align': 'right'})

        rows = []
        for d in sorted(matrix.keys()):
            kwh_vals = matrix[d]
            total_kwh = sum(kwh_vals)
            cost_val = cost_table.get_cost(d)
            total_cost = total_kwh * cost_val

            row = [d, f"{total_cost:.2f}", f"{total_kwh:.3f}"]
            for val in kwh_vals:
                row.append(f"{val:.3f}")
            rows.append(row)
            
        printTable(header, rows, indent=indent)

    def summary(self):
        print("\n# Daily Table\n")
        macs = self.get_all_macs()
        if not macs:
            print("  No daily data found.")
            return
            
        for mac in macs:
            print(f"  MAC: {mac}")
            self.print_daily_matrix(mac, self.db.costs, indent="  ")


class CostTable(Table):
    def insert(self, valid_from: str, price: float):
        self.db.execute_write("REPLACE INTO cost (valid_from, price) VALUES (?, ?)", (valid_from, price))

    def get_cost(self, date_str: str) -> float:
        rows = self.db.execute_read("SELECT price FROM cost WHERE valid_from <= ? ORDER BY valid_from DESC LIMIT 1", (date_str,))
        return float(rows[0]['price']) if rows else 0.0

    def get_all(self):
        return self.db.execute_read("SELECT * FROM cost ORDER BY valid_from ASC")

    def summary(self):
        print("\n# Cost Table\n")
        rows = [[r['valid_from'], f"{r['price']:.3f}"] for r in self.get_all()]
        header = [
            {'primary': 'Valid From'},
            {'primary': 'Price ($/kWh)', 'align': 'right'}
        ]
        printTable(header, rows, indent="  ")


class PowerDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        self.strips = StripTable(self, """
            strips (
                mac_address TEXT PRIMARY KEY,
                number INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        
        self.devices = DeviceTable(self, """
            devices (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        
        self.mappings = DeviceMappingTable(self, """
            device_mapping (
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
        
        self.telemetry = TelemetryTable(self, """
            telemetry (
                timestamp TEXT NOT NULL,
                mac_address TEXT NOT NULL,
                plug_index INTEGER NOT NULL,
                watts REAL NOT NULL,
                volts REAL NOT NULL,
                amps REAL NOT NULL,
                PRIMARY KEY (timestamp, mac_address, plug_index)
            )
        """)
        
        self.daily = DailyTable(self, """
            daily (
                date TEXT NOT NULL,
                mac_address TEXT NOT NULL,
                plug_index INTEGER NOT NULL,
                kwh REAL NOT NULL,
                PRIMARY KEY (date, mac_address, plug_index)
            )
        """)
        
        self.costs = CostTable(self, """
            cost (
                valid_from TEXT PRIMARY KEY,
                price REAL
            )
        """)
        
        self._initialize_schema()

    def _initialize_schema(self):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            with conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.strips.schema)
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.devices.schema)
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.costs.schema)
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.mappings.schema)
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.telemetry.schema)
                cursor.execute("CREATE TABLE IF NOT EXISTS " + self.daily.schema)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp)")

    def execute_read(self, query: str, params: tuple = ()):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()

    def execute_write(self, query: str, params: tuple = ()):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            with conn:
                conn.execute(query, params)


class TimeSeries:
    def __init__(self, data: list):
        self._data = data
    def points(self):
        return [(r['timestamp'], r['watts'], r['volts'], r['amps']) for r in self._data]
    def average_watts(self):
        if not self._data: return 0.0
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

    def uid(self): return self._uid
    def name(self): return self._name
    def description(self): return self._description


class Strip:
    def __init__(self, db: PowerDB, mac_address: str):
        self._db = db
        self._mac = mac_address
        rows = db.execute_read("SELECT number, name, description FROM strips WHERE mac_address = ?", (mac_address,))
        if not rows:
            raise ValueError(f"Strip MAC '{mac_address}' does not exist in the database.")
        self._number = rows[0]['number']
        self._name = rows[0]['name']
        self._description = rows[0]['description']

    def mac(self): return self._mac
    def number(self): return self._number
    def name(self): return self._name


class Env:
    def __init__(self, db: PowerDB):
        self.db = db
        self._devices = {}
        self._strips_mapping = {}
        self.refresh()

    def refresh(self):
        self._devices.clear()
        for row in self.db.devices.get_all():
            uid = row['uid']
            self._devices[uid] = Device(self.db, uid)

        self._strips_mapping.clear()
        for row in self.db.execute_read("SELECT mac_address FROM strips"):
            mac = row['mac_address']
            strip = Strip(self.db, mac)
            self._strips_mapping[mac] = strip
            self._strips_mapping[strip.name()] = strip
            self._strips_mapping[strip.number()] = strip
            self._strips_mapping[str(strip.number())] = strip

    def get_device(self, identifier: str) -> Device:
        if identifier in self._devices:
            return self._devices[identifier]
        for dev in self._devices.values():
            if dev.name() == identifier:
                return dev
        return None

    def get_strip(self, identifier) -> Strip:
        if identifier in self._strips_mapping:
            return self._strips_mapping[identifier]
        try:
            if int(identifier) in self._strips_mapping:
                return self._strips_mapping[int(identifier)]
        except ValueError:
            pass
        return None

# ==============================================================================
# OPERATIONS
# ==============================================================================

def bootstrap_db(db: PowerDB):
    db.devices.insert("empty", "Empty", "No physical device connected")
    db.costs.insert("2026-05-01", 0.084)
    
    if not SEED_DATA:
        return

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for idx, (mac, strip_info) in enumerate(SEED_DATA.items(), start=1):
        db.strips.insert(mac, idx, strip_info['name'], "Bootstrapped from seed data")
        
        for plug_idx, (uid, name, desc) in enumerate(strip_info['devices']):
            db.devices.insert(uid, name, desc)
            db.devices.update(uid, name, desc)
            
            existing = db.mappings.get_active(mac, plug_idx)
            if not existing:
                db.mappings.map_device(mac, plug_idx, uid, current_time)


async def poll_devices(env: Env, target_strip_arg: str = None):
    target_strip = None
    if target_strip_arg:
        target_strip = env.get_strip(target_strip_arg)
        if not target_strip:
            print(f"[!] Warning: Target strip '{target_strip_arg}' does not exist in the environment.")
            return

    print("Initiating Kasa device poll...\n")
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_local = datetime.now()
    yesterday_str = (now_local - timedelta(days=1)).strftime("%Y-%m-%d")

    months_to_fetch = [(now_local.year, now_local.month)]
    prev_month = now_local.month - 1
    prev_year = now_local.year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    months_to_fetch.append((prev_year, prev_month))

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
            
            has_yesterday = env.db.execute_read("SELECT 1 FROM daily WHERE mac_address = ? AND date = ? LIMIT 1", (mac, yesterday_str))
            fetch_daily = not bool(has_yesterday)

            resolved_strip = env.get_strip(mac)
            if not resolved_strip:
                if mac in SEED_DATA:
                    next_num = len(env.db.strips.get_all()) + 1
                    env.db.strips.insert(mac, next_num, SEED_DATA[mac]['name'], "Auto-discovered strip")
                    for plug_idx, (uid, name, desc) in enumerate(SEED_DATA[mac]['devices']):
                        env.db.devices.insert(uid, name, desc)
                        env.db.devices.update(uid, name, desc)
                        env.db.mappings.map_device(mac, plug_idx, uid, current_time)
                    env.refresh() 
                    resolved_strip = env.get_strip(mac)
                else:
                    print(f"[!] Warning: Discovered unconfigured MAC address {mac}.")
                    continue

            if target_strip and mac != target_strip.mac():
                continue

            print(f"Strip [{resolved_strip.number()}] MAC: {mac} | Time: {current_time}")
            
            header = [
                {'primary': '#'},
                {'primary': 'Power', 'secondary': '(W)', 'align': 'right'},
                {'primary': 'Voltage', 'secondary': '(V)', 'align': 'right'},
                {'primary': 'Current', 'secondary': '(A)', 'align': 'right'},
                {'primary': 'Device', 'secondary': '(uid)'},
                {'primary': 'Device', 'secondary': '(name)'}
            ]
            
            rows = []
            for plug_idx, plug in enumerate(device.children):
                energy = plug.modules[Module.Energy]
                power = float(getattr(energy, 'current_consumption', getattr(energy, 'power', 0.0)))
                voltage = float(energy.voltage)
                current = float(energy.current)

                env.db.telemetry.insert(current_time, mac, plug_idx, power, voltage, current)
                mapping = env.db.mappings.get_active(mac, plug_idx)
                dev_uid = mapping['device_uid'] if mapping else "empty"
                
                dev_name = "Empty"
                if mapping:
                    dev_row = env.db.execute_read("SELECT name FROM devices WHERE uid=?", (dev_uid,))
                    if dev_row: dev_name = dev_row[0]['name']

                rows.append([str(plug_idx), f"{power:.3f}", f"{voltage:.3f}", f"{current:.3f}", dev_uid, dev_name])

                if fetch_daily:
                    for y, m in months_to_fetch:
                        res = await energy.get_daily_stats(year=y, month=m)
                        for day, kwh in res.items():
                            date_str = f"{y:04d}-{m:02d}-{int(day):02d}"
                            env.db.daily.upsert(date_str, mac, plug_idx, float(kwh))

            printTable(header, rows)
            print()

            if fetch_daily:
                print(f"Daily Energy Aggregates Acquired for MAC: {mac}")
                env.db.daily.print_daily_matrix(mac, env.db.costs)
                print()

    except Exception as e:
        print(f"Error during polling: {e}")


async def _daemon_loop(env: Env, device, offset: int):
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
                env.db.telemetry.insert(current_time, mac, idx, power, voltage, current)
        except Exception as e:
            print(f"[DAEMON] Error polling strip {mac}: {e}")
            
        await asyncio.sleep(15)


async def run_daemon(env: Env):
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
        
        if not env.get_strip(mac) and mac not in SEED_DATA:
            print(f"[DAEMON] Skipping unconfigured strip: {mac}")
            continue
            
        offset = idx * 5
        tasks.append(asyncio.create_task(_daemon_loop(env, device, offset)))

    print(f"[DAEMON] Discovery complete. {len(tasks)} strips targeted. Entering infinite poll loop.")
    await asyncio.gather(*tasks)


def cli_move(env: Env, uid: str, strip_arg: str, plug: int, date_str: str):
    try:
        timestamp_str = parse_local_to_utc_iso(date_str)
        dt_utc = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as e:
        print(f"[!] {e}")
        return

    curr_uid = uid
    curr_strip_arg = strip_arg
    curr_plug = plug
    
    known_old_loc_str = None

    while True:
        timestamp = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if curr_strip_arg.lower() == 'unplugged':
            if known_old_loc_str:
                old_str = known_old_loc_str
            else:
                old_loc = env.db.execute_read("SELECT mac_address, plug_index FROM device_mapping WHERE device_uid = ? AND valid_to IS NULL", (curr_uid,))
                if old_loc:
                    old_strip = env.get_strip(old_loc[0]['mac_address'])
                    if old_strip:
                        old_str = f"Strip {old_loc[0]['mac_address']} (#{old_strip.number()}, {old_strip.name()}) Plug {old_loc[0]['plug_index']}"
                    else:
                        old_str = f"Strip {old_loc[0]['mac_address']} Plug {old_loc[0]['plug_index']}"
                else:
                    old_str = "an unmapped state"
                    
            old_loc = env.db.execute_read("SELECT mac_address, plug_index FROM device_mapping WHERE device_uid = ? AND valid_to IS NULL", (curr_uid,))
            if old_loc:
                env.db.mappings.map_device(old_loc[0]['mac_address'], old_loc[0]['plug_index'], 'empty', timestamp)
            print(f"Device {curr_uid} moved from {old_str} to an unplugged state at {timestamp}.")
            break
            
        strip = env.get_strip(curr_strip_arg)
        if not strip:
            print(f"[!] Error: Strip '{curr_strip_arg}' not found.")
            return
            
        mac = strip.mac()
        
        existing = env.db.mappings.get_active(mac, curr_plug)
        evicted_uid = None
        if existing and existing['device_uid'] not in ('empty', curr_uid):
            evicted_uid = existing['device_uid']

        if known_old_loc_str:
            old_str = known_old_loc_str
        else:
            old_loc = env.db.execute_read("SELECT mac_address, plug_index FROM device_mapping WHERE device_uid = ? AND valid_to IS NULL", (curr_uid,))
            if old_loc:
                old_strip = env.get_strip(old_loc[0]['mac_address'])
                if old_strip:
                    old_str = f"Strip {old_loc[0]['mac_address']} (#{old_strip.number()}, {old_strip.name()}) Plug {old_loc[0]['plug_index']}"
                else:
                    old_str = f"Strip {old_loc[0]['mac_address']} Plug {old_loc[0]['plug_index']}"
            else:
                old_str = "an unmapped state"

        env.db.mappings.map_device(mac, curr_plug, curr_uid, timestamp)
        print(f"Device {curr_uid} moved from {old_str} to Strip {mac} (#{strip.number()}, {strip.name()}) Plug {curr_plug} at {timestamp}.")

        if evicted_uid:
            evicted_dev = env.get_device(evicted_uid)
            evicted_name = evicted_dev.name() if evicted_dev else evicted_uid
            
            print(f"\n[!] Move conflict: Device '{evicted_name}' ({evicted_uid}) was evicted from Strip {mac} Plug {curr_plug}.")
            ans = input(f"Where should '{evicted_name}' be moved to? (Enter 'strip_name plug_index' or 'unplugged'): ").strip()
            
            known_old_loc_str = f"Strip {mac} (#{strip.number()}, {strip.name()}) Plug {curr_plug}"
            
            if ans.lower() == 'unplugged':
                curr_uid = evicted_uid
                curr_strip_arg = 'unplugged'
                curr_plug = -1
            else:
                parts = ans.rsplit(' ', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    curr_uid = evicted_uid
                    curr_strip_arg = parts[0]
                    curr_plug = int(parts[1])
                else:
                    print("Invalid input. Treating as 'unplugged'.")
                    curr_uid = evicted_uid
                    curr_strip_arg = 'unplugged'
                    curr_plug = -1
                    
            dt_utc += timedelta(seconds=1)
        else:
            break


def cli_rename(env: Env, uid: str, new_name: str, desc: str = None):
    d = env.get_device(uid)
    if not d:
        print(f"Error: Device {uid} not found.")
        return
    desc = desc if desc else d.description()
    env.db.devices.update(uid, new_name, desc)
    print(f"Device {uid} renamed to '{new_name}'.")


def cli_query(env: Env, start_str: str, end_str: str, device_filter: str, strip_filter: str):
    now = datetime.now(timezone.utc)
    try:
        start_iso = parse_local_to_utc_iso(start_str) if start_str else (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = parse_local_to_utc_iso(end_str) if end_str else now.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        print(f"[!] Error parsing dates: {e}")
        return

    device_re = re.compile(device_filter) if device_filter else None
    strip_re = re.compile(strip_filter) if strip_filter else None

    raw_rows = env.db.telemetry.get_range(start_iso, end_iso)
    
    print(f"Query Range (UTC limits): {start_iso} to {end_iso}")
    
    header = [
        {'primary': 'Date'},
        {'primary': 'Power', 'secondary': '(W)', 'align': 'right'},
        {'primary': 'Voltage', 'secondary': '(V)', 'align': 'right'},
        {'primary': 'Current', 'secondary': '(A)', 'align': 'right'},
        {'primary': 'Device', 'secondary': '(uid)'},
        {'primary': 'Strip', 'secondary': '(name)'}
    ]

    rows = []
    for r in raw_rows:
        dev_uid = r['device_uid']
        strip_name = r['strip_name']

        if device_re and not device_re.search(dev_uid): continue
        if strip_re and not strip_re.search(strip_name): continue
            
        dt_str = format_utc_to_local(r['timestamp'])
        rows.append([dt_str, f"{r['watts']:.3f}", f"{r['volts']:.3f}", f"{r['amps']:.3f}", dev_uid, strip_name])

    printTable(header, rows)
    print(f"Total records retrieved: {len(raw_rows)} (Displayed: {len(rows)})\n")


def cli_price(env: Env, start_str: str, price: float):
    if not start_str:
        start_str = datetime.now().strftime("%Y-%m-%d")
        
    if price == 0.0:
        try:
            user_input = input(f"Enter price per kWh for valid_from date {start_str}: ")
            price = float(user_input)
        except ValueError:
            print("Error: Invalid price entered. Must be a float.")
            return

    env.db.costs.insert(start_str, price)
    print(f"Cost Table updated: {start_str} -> ${price:.3f}/kWh")


def cli_backup(env: Env, target_path: str, bucket_name: str):
    print("Initiating database backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = os.path.basename(env.db.db_path)
    tmp_backup_path = f"/tmp/{db_filename}.{timestamp}.bak"

    try:
        with contextlib.closing(sqlite3.connect(env.db.db_path)) as src, contextlib.closing(sqlite3.connect(tmp_backup_path)) as dst:
            src.backup(dst)
        print(f"[+] Local snapshot created at {tmp_backup_path}")
    except Exception as e:
        print(f"[!] Failed to snapshot database: {e}")
        return

    if not os.path.exists(target_path):
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
            blob = bucket.blob(os.path.basename(tmp_backup_path))
            blob.upload_from_filename(tmp_backup_path)
            print(f"[+] GCP upload complete: gs://{bucket_name}/{blob.name}")
        except ImportError:
            print("[!] GCP Upload skipped: 'google-cloud-storage' library not installed.")
        except Exception as e:
            print(f"[!] GCP Upload failed: {e}")
            
    try:
        os.remove(tmp_backup_path)
    except OSError:
        pass
    print("Backup sequence finished.")


def cli_state(env: Env):
    print("DATABASE STATE")
    print("==============\n")
    env.db.strips.summary()
    env.db.devices.summary()
    env.db.costs.summary()
    env.db.mappings.summary()
    env.db.telemetry.summary()
    env.db.daily.summary()

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

    parser_daemon = subparsers.add_parser('daemon', help="Run continuous polling daemon (for systemd)")

    parser_poll = subparsers.add_parser('poll', help="Poll network for Kasa strips and log telemetry")
    parser_poll.add_argument('-s', '--strip', type=str, default=None, help="Specific strip index, name, or MAC to poll. Defaults to all.")

    parser_move = subparsers.add_parser('move', help="Map a device to a specific physical strip and plug")
    parser_move.add_argument('uid', type=str, help="Device UID")
    parser_move.add_argument('strip', type=str, help="Strip MAC Address, Name, Number, or 'unplugged'")
    parser_move.add_argument('plug', type=int, nargs='?', default=-1, help="Plug Index (0-5) (omit if unplugging)")
    parser_move.add_argument('--date', type=str, default="now", help="Date/time of move (YYYY-mm-dd HH:MM:SS). Defaults to 'now'.")

    parser_rename = subparsers.add_parser('rename', help="Rename a device")
    parser_rename.add_argument('uid', type=str, help="Device UID")
    parser_rename.add_argument('name', type=str, help="New Human-Readable Name")
    parser_rename.add_argument('--desc', type=str, help="New Description", default=None)

    parser_query = subparsers.add_parser('query', help="Query telemetry data for a given date range")
    parser_query.add_argument('-b', '--start', type=str, default="", help="Start date (YYYY-mm-dd [HH:MM[:SS]])")
    parser_query.add_argument('-e', '--end', type=str, default="", help="End date (YYYY-mm-dd [HH:MM[:SS]])")
    parser_query.add_argument('-d', '--device', type=str, default="", help="Regex filter for Device uid")
    parser_query.add_argument('-s', '--strip', type=str, default="", help="Regex filter for Strip name")

    parser_price = subparsers.add_parser('price', help="Update the cost per kWh threshold")
    parser_price.add_argument('--start', type=str, default="", help="Start date (YYYY-mm-dd). Defaults to today.")
    parser_price.add_argument('--price', type=float, default=0.0, help="New price in dollars. Defaults to prompting user.")

    parser_backup = subparsers.add_parser('backup', help="Safe snapshot and backup of SQLite database")
    parser_backup.add_argument('--path', type=str, required=True, help="Local directory path to rsync backup file to")
    parser_backup.add_argument('--bucket', type=str, default=None, help="GCP Bucket name for cloud storage upload")

    parser_state = subparsers.add_parser('state', help="Print the current state of the database schemas")

    args = parser.parse_args()

    if args.command == 'daemon':
        asyncio.run(run_daemon(env))
    elif args.command == 'poll':
        asyncio.run(poll_devices(env, args.strip))
    elif args.command == 'move':
        cli_move(env, args.uid, args.strip, args.plug, args.date)
    elif args.command == 'rename':
        cli_rename(env, args.uid, args.name, args.desc)
    elif args.command == 'query':
        cli_query(env, args.start, args.end, args.device, args.strip)
    elif args.command == 'price':
        cli_price(env, args.start, args.price)
    elif args.command == 'backup':
        cli_backup(env, args.path, args.bucket)
    elif args.command == 'state':
        cli_state(env)
