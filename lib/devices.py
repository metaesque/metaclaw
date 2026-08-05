# ==============================================================================
# META<CLAW> DEVICES API
# ==============================================================================

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

class PowerStrip(Device):
    """
    Represents a smart power strip (e.g., Kasa HS300) capable of energy monitoring.
    """
    def get_mac_address(self):
        return self.data.get("mac_address")

    def get_plugs(self):
        return self.data.get("plugs", {})

