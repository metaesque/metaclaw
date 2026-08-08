#!/usr/bin/env python3
"""
Management script for setting and updating the electricity_price_cad_per_kwh
time-series metric in VictoriaMetrics.
"""

import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

VM_WRITE_URL = "http://127.0.0.1:8428/write"

def parse_args():
    parser = argparse.ArgumentParser(description="Inject electricity price metric into VictoriaMetrics.")
    parser.add_argument("--price", type=float, required=True, help="Price per kWh in CAD (e.g. 0.0845)")
    parser.add_argument("--date", type=str, default=None, help="Effective date YYYY-MM-DD (defaults to current time)")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.date:
        try:
            dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            timestamp_ns = int(dt.timestamp() * 1e9)
        except ValueError:
            print("ERROR: Date format must be YYYY-MM-DD")
            sys.exit(1)
    else:
        timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)

    # Influx Line Protocol: Sending 'electricity_price_cad_per_kwh=val' with no measurement
    # ensures VictoriaMetrics registers the metric name exactly as electricity_price_cad_per_kwh.
    payload = f"electricity_price_cad_per_kwh={args.price} {timestamp_ns}\n".encode('utf-8')

    req = urllib.request.Request(VM_WRITE_URL, data=payload, headers={"Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 204):
                date_str = args.date if args.date else "NOW"
                print(f"SUCCESS: Successfully recorded price ${args.price:.4f} CAD/kWh for effective timestamp [{date_str}].")
            else:
                print(f"ERROR: VictoriaMetrics returned status code {resp.status}")
                sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to communicate with VictoriaMetrics at {VM_WRITE_URL}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

