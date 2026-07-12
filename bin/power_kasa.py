import asyncio
import os
import json
import argparse
import warnings
from datetime import datetime, timedelta
from kasa import Discover, DeviceType, Module

# Empirically verified mapping for compute/control nodes.
# Best-guess mapping for router/switch based on baseline power draws.
DEVICE_MAPPING = {
    0: "Shaw Router",
    1: "Unknown",
    2: "Empty",
    3: "compute (EVO-X2)",
    4: "control (K8 Plus)",
    5: "Binardat Switch"
}

def get_last_record(filepath):
    """Retrieves the last JSON record from the .jsonl file, if it exists."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if lines:
                return json.loads(lines[-1])
    except Exception:
        return None
    return None

async def discover_kasa_devices(fetch_summary=False):
    """
    Discovers TP-Link Kasa devices on the local network.
    Renders telemetry data for Power Strips (like the HS300) in a concise table
    and appends a JSON state object to the historical data log.
    If fetch_summary is True, retrieves historical daily data up to yesterday.
    """
    print("Initiating Kasa device discovery...\n")

    # Resolve absolute path to bin/data regardless of where the user runs the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    data_file = os.path.join(data_dir, "metaclaw_power.jsonl")

    current_date_str = datetime.now().strftime("%Y%m%dT%H%M%S")
    last_record = get_last_record(data_file)

    last_data = last_record.get("data", {}) if last_record else {}
    last_date_str = last_record.get("date", "Never") if last_record else "Never"

    try:
        # Discover.discover() returns a dictionary of {ip_address: SmartDevice_instance}
        found_devices = await Discover.discover(timeout=5)

        if not found_devices:
            print("Discovery complete. No Kasa devices found.")
            print("Troubleshooting:")
            print("1. Ensure the script is running on a node physically inside the local network (not over Tailscale from a Mac).")
            print("2. Check if the Kasa HS300 is powered on and actively connected to the Wi-Fi.")
            return

        for ip_address, device in found_devices.items():
            # Update the device state to ensure we have the latest telemetry
            await device.update()

            # Check if the device supports real-time energy monitoring and is a power strip
            if Module.Energy in device.modules and device.device_type == DeviceType.Strip:
                print(f"Previous Data Time : {last_date_str}")
                print(f"Current Data Time  : {current_date_str}\n")

                print("-" * 105)
                print(f"{'Plug':<4} | {'Power (W)':>9} | {'ΔPower':>8} | {'Voltage (V)':>11} | {'ΔVoltage':>9} | {'Current (A)':>11} | {'ΔCurrent':>9} | {'Device':<25}")
                print("-" * 105)

                current_json_record = {
                    "date": current_date_str,
                    "data": {}
                }

                # Enumerate through the 6 outlets on the HS300
                for idx, plug in enumerate(device.children):
                    energy = plug.modules[Module.Energy]
                    # Handle backwards compatibility for 'power' vs 'current_consumption'
                    power = float(getattr(energy, 'current_consumption', getattr(energy, 'power', 0.0)))
                    voltage = float(energy.voltage)
                    current = float(energy.current)

                    device_name = DEVICE_MAPPING.get(idx, "Unmapped")

                    # Calculate deltas based on previous run, defaulting to 0.0 if missing
                    prev_plug = last_data.get(str(idx), {})
                    d_power = power - float(prev_plug.get("watts", power))
                    d_voltage = voltage - float(prev_plug.get("volts", voltage))
                    d_current = current - float(prev_plug.get("amps", current))

                    current_json_record["data"][str(idx)] = {
                        "watts": power,
                        "volts": voltage,
                        "amps": current,
                        "device": device_name
                    }

                    print(f"{idx:<4} | {power:>9.3f} | {d_power:>8.3f} | {voltage:>11.3f} | {d_voltage:>9.3f} | {current:>11.3f} | {d_current:>9.3f} | {device_name:<25}")

                print("-" * 105)
                print()

                # Append the JSON payload to the data file
                with open(data_file, 'a') as f:
                    f.write(json.dumps(current_json_record) + "\n")

                if fetch_summary:
                    print("\n" + "=" * 90)
                    print("Fetching historical summary data from Jan 2020 to yesterday...")
                    summary_file = os.path.join(data_dir, "metaclaw_power.json")

                    # Load existing data to avoid overwriting
                    all_history = {}
                    if os.path.exists(summary_file):
                        try:
                            with open(summary_file, 'r') as f:
                                all_history = json.load(f)
                        except json.JSONDecodeError:
                            pass

                    start_year, start_month = 2020, 1
                    yesterday = datetime.now() - timedelta(days=1)
                    end_year, end_month = yesterday.year, yesterday.month

                    for idx, plug in enumerate(device.children):
                        device_name = DEVICE_MAPPING.get(idx, "Unmapped")
                        curr_y, curr_m = start_year, start_month

                        while curr_y < end_year or (curr_y == end_year and curr_m <= end_month):
                            try:
                                # Suppress the deprecation warning and use the known-working API
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore", DeprecationWarning)
                                    if hasattr(plug, 'get_emeter_daily'):
                                        res = await plug.get_emeter_daily(year=curr_y, month=curr_m)
                                    else:
                                        res = {}

                                if res:
                                    for day, kwh in res.items():
                                        # Only add days up to yesterday
                                        if curr_y == end_year and curr_m == end_month and int(day) > yesterday.day:
                                            continue

                                        date_str = f"{curr_y:04d}-{curr_m:02d}-{int(day):02d}"
                                        if date_str not in all_history:
                                            all_history[date_str] = {}
                                        all_history[date_str][str(idx)] = {
                                            "kwh": float(kwh),
                                            "device": device_name
                                        }
                            except Exception:
                                pass # Silently skip exceptions for missing data ranges

                            curr_m += 1
                            if curr_m > 12:
                                curr_m = 1
                                curr_y += 1

                    with open(summary_file, 'w') as f:
                        json.dump(all_history, f, indent=2, sort_keys=True)

                    print("-" * 69)
                    print(f"{'Year':<4} | {'Mon':<3} | {'Day':<3} | {'router':>7} | {'switch':>7} | {'compute':>7} | {'control':>7} | {'Total':>7} |")
                    print("-" * 69)

                    prev_y, prev_m = None, None
                    for date_str in sorted(all_history.keys()):
                        y, m, d = date_str.split('-')

                        # Transitive blanking
                        disp_y = y if y != prev_y else ""
                        disp_m = m if (m != prev_m or y != prev_y) else ""
                        prev_y, prev_m = y, m

                        day_data = all_history[date_str]

                        router = day_data.get("0", {}).get("kwh", 0.0)
                        compute = day_data.get("3", {}).get("kwh", 0.0)
                        control = day_data.get("4", {}).get("kwh", 0.0)
                        switch = day_data.get("5", {}).get("kwh", 0.0)

                        total = router + switch + compute + control

                        print(f"{disp_y:<4} | {disp_m:<3} | {d:<3} | {router:>7.3f} | {switch:>7.3f} | {compute:>7.3f} | {control:>7.3f} | {total:>7.3f}")

                    print("-" * 90)
                    print(f"\n[+] Historical summary saved to {summary_file}")
                    print("=" * 90 + "\n")

            else:
                print(f"\n[!] Device {device.alias} is not a power strip or does not support energy monitoring.")

    except Exception as e:
        print(f"An error occurred during discovery: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kasa Power Discovery and Telemetry")
    parser.add_argument('-s', '--summary', action='store_true', help="Fetch historical daily summaries from Jan 2020 to yesterday.")
    args = parser.parse_args()
    asyncio.run(discover_kasa_devices(args.summary))
