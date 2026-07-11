import asyncio
import os
import json
from datetime import datetime
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

async def discover_kasa_devices():
    """
    Discovers TP-Link Kasa devices on the local network.
    Renders telemetry data for Power Strips (like the HS300) in a concise table
    and appends a JSON state object to the historical data log.
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

            else:
                print(f"\n[!] Device {device.alias} is not a power strip or does not support energy monitoring.")

    except Exception as e:
        print(f"An error occurred during discovery: {e}")

if __name__ == "__main__":
    asyncio.run(discover_kasa_devices())
