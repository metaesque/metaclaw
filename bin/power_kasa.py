import asyncio
from kasa import Discover

async def discover_kasa_devices():
    """
    Discovers TP-Link Kasa devices on the local network.
    Includes basic error handling for timeout and network issues.
    """
    print("Initiating Kasa device discovery on the local network...")
    print("This sends UDP broadcast packets on port 9999.\n")

    try:
        # Discover.discover() returns a dictionary of {ip_address: SmartDevice_instance}
        # timeout is in seconds
        found_devices = await Discover.discover(timeout=5)

        if not found_devices:
            print("Discovery complete. No Kasa devices found.")
            print("Troubleshooting:")
            print("1. Ensure the GMKtec computer is on the exact same VLAN/subnet as the Kasa devices.")
            print("2. Verify that UDP broadcasts on port 9999 are not blocked by a local firewall.")
            print("3. Check if the Kasa HS300 is powered on and actively connected to the Wi-Fi.")
            return

        print(f"Discovery complete. Found {len(found_devices)} device(s):\n")

        for ip_address, device in found_devices.items():
            # Update the device state to ensure we have the latest telemetry before querying
            await device.update()

            print("-" * 40)
            print(f"Alias/Name : {device.alias}")
            print(f"IP Address : {ip_address}")
            print(f"Model      : {device.model}")
            print(f"MAC Address: {device.mac}")

            # Check if the device supports real-time energy monitoring
            if device.has_emeter:
                print("Emeter     : Supported")

                # If it's a strip (like the HS300), iterate through its children (outlets)
                if device.is_strip:
                    print("Type       : Power Strip")
                    for plug in device.children:
                        print(f"  -> Outlet '{plug.alias}':")
                        print(f"     Power  : {plug.emeter_realtime.power} W")
                        print(f"     Voltage: {plug.emeter_realtime.voltage} V")
                        print(f"     Current: {plug.emeter_realtime.current} A")
                else:
                    print(f"Power      : {device.emeter_realtime.power} W")
                    print(f"Voltage    : {device.emeter_realtime.voltage} V")
                    print(f"Current    : {device.emeter_realtime.current} A")
            else:
                print("Emeter     : Not Supported")

    except Exception as e:
        print(f"An error occurred during discovery: {e}")

if __name__ == "__main__":
    asyncio.run(discover_kasa_devices())
