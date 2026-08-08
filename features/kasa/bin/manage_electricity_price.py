#!/usr/bin/env python3
"""
Management script for setting, updating, verifying, and dumping the
electricity_price_cad_per_kwh time-series metric in VictoriaMetrics.
"""

import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

VM_BASE_URL = "http://127.0.0.1:8428"
METRIC_NAME = "electricity_price_cad_per_kwh"


def parse_args():
    parser = argparse.ArgumentParser(description="Manage electricity price metric in VictoriaMetrics.")
    parser.add_argument("--price", type=float, help="Price per kWh in CAD (e.g. 0.0845)")
    parser.add_argument("--date", type=str, default=None, help="Effective date YYYY-MM-DD (defaults to current time)")
    parser.add_argument("--dump", action="store_true", help="Dump all historical price entries in an ASCII table")
    return parser.parse_args()


def dump_history():
    """Queries VictoriaMetrics export endpoint and renders all points in a pretty ASCII table."""
    url = f"{VM_BASE_URL}/api/v1/export?match[]={METRIC_NAME}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            lines = resp.read().decode('utf-8').strip().split('\n')

            points = []
            for line in lines:
                if not line:
                    continue
                data = json.loads(line)
                values = data.get('values', [])
                timestamps = data.get('timestamps', [])
                for val, ts_ms in zip(values, timestamps):
                    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                    points.append((dt.strftime("%Y-%m-%d %H:%M:%S UTC"), val))

            if not points:
                print(f"No historical records found for metric '{METRIC_NAME}'.")
                return

            # Print ASCII Table
            print("+-------------------------+---------------+")
            print("| Effective Date (UTC)    | Price (CAD)   |")
            print("+-------------------------+---------------+")
            for dt_str, val in sorted(points, key=lambda x: x[0]):
                print(f"| {dt_str:<23} | ${val:<12.4f} |")
            print("+-------------------------+---------------+")

    except Exception as e:
        print(f"ERROR: Failed to dump history from VictoriaMetrics: {e}")
        sys.exit(1)


def verify_write(expected_price, timestamp_ms):
    """Verifies that the written point actually exists in VictoriaMetrics."""
    # Query export endpoint for exact validation
    url = f"{VM_BASE_URL}/api/v1/export?match[]={METRIC_NAME}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            lines = resp.read().decode('utf-8').strip().split('\n')
            for line in lines:
                if not line:
                    continue
                data = json.loads(line)
                values = data.get('values', [])
                timestamps = data.get('timestamps', [])
                for val, ts_ms in zip(values, timestamps):
                    if abs(ts_ms - timestamp_ms) < 1000 and abs(val - expected_price) < 1e-5:
                        return True
        return False
    except Exception:
        return False


def main():
    args = parse_args()

    if args.dump:
        dump_history()
        return

    if args.price is None:
        print("ERROR: Must specify either --price or --dump.")
        sys.exit(1)

    if args.date:
        try:
            dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            timestamp_ms = int(dt.timestamp() * 1000)
        except ValueError:
            print("ERROR: Date format must be YYYY-MM-DD")
            sys.exit(1)
    else:
        dt = datetime.now(timezone.utc)
        timestamp_ms = int(dt.timestamp() * 1000)

    # Use native VictoriaMetrics Prometheus import format: <metric_name> <value> <timestamp_ms>
    payload = f"{METRIC_NAME} {args.price} {timestamp_ms}\n".encode('utf-8')
    import_url = f"{VM_BASE_URL}/api/v1/import/prometheus"

    req = urllib.request.Request(import_url, data=payload, headers={"Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 204):
                print(f"ERROR: VictoriaMetrics returned HTTP status {resp.status}")
                sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to write to VictoriaMetrics at {import_url}: {e}")
        sys.exit(1)

    # Round-trip Verification Step
    date_str = args.date if args.date else dt.strftime("%Y-%m-%d")
    print(f"[Write] Submitted ${args.price:.4f} CAD/kWh for [{date_str}]. Verifying...")

    if verify_write(args.price, timestamp_ms):
        print(f"SUCCESS: Verified write against VictoriaMetrics for timestamp [{date_str}].")
    else:
        print("FATAL: Verification failed! VictoriaMetrics did not return the written data point.")
        sys.exit(1)


if __name__ == "__main__":
    main()
