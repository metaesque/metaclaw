import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Inject the lib directory directly to support module mapping
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
from devices import (
    Device, ExternalSSD, NetworkUplink,
    PowerAsset, ComputeNode, PowerStrip
)

class TestDevice(unittest.TestCase):
    def test___init__(self):
        uid = "test_dev"
        data = {"name": "Test Device", "type": "generic", "location": "Lab"}
        dev = Device(uid, data)
        self.assertEqual(dev.uid, uid)
        self.assertEqual(dev.name, "Test Device")
        self.assertEqual(dev.device_type, "generic")
        self.assertEqual(dev.location, "Lab")

    def test_get_info(self):
        uid = "test_dev"
        data = {"name": "Test Device", "type": "generic", "location": "Lab"}
        dev = Device(uid, data)
        info = dev.get_info()
        self.assertEqual(info['uid'], uid)
        self.assertEqual(info['name'], "Test Device")

class TestExternalSSD(unittest.TestCase):
    def test___init__(self):
        dev = ExternalSSD("t7", {"type": "ssd"})
        self.assertEqual(dev.device_type, "ssd")

class TestNetworkUplink(unittest.TestCase):
    def test___init__(self):
        dev = NetworkUplink("switch", {"type": "network"})
        self.assertEqual(dev.device_type, "network")

class TestPowerAsset(unittest.TestCase):
    def test___init__(self):
        dev = PowerAsset("ups", {"type": "power"})
        self.assertEqual(dev.device_type, "power")

class TestComputeNode(unittest.TestCase):
    def setUp(self):
        self.data = {
            "name": "test_node",
            "type": "node",
            "processing": {"cpu": 8},
            "vram": {"size": 32},
            "bandwidth": 100.0,
            "mounts": [
                {"mountpoint": "/mnt/test", "uuid": "1234-5678", "fstype": "ext4"}
            ]
        }
        self.node = ComputeNode("test_node", self.data)

    def test___init__(self):
        self.assertEqual(self.node.uid, "test_node")

    def test_get_hardware_specs(self):
        specs = self.node.get_hardware_specs()
        self.assertEqual(specs["processing"]["cpu"], 8)
        self.assertEqual(specs["vram"]["size"], 32)
        self.assertEqual(specs["bandwidth_gbps"], 100.0)

    @patch('devices.socket.gethostname', return_value='test_node')
    @patch('devices.subprocess.run')
    def test_update_data(self, mock_run, mock_hostname):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"blockdevices": []}'
        mock_run.return_value = mock_result

        self.node.update_data()
        self.assertIn('_live_lsblk', self.node.data)

    @patch('devices.os.path.ismount', return_value=False)
    @patch('devices.os.makedirs')
    @patch('devices.subprocess.run')
    def test_mount_storage(self, mock_run, mock_makedirs, mock_ismount):
        self.node.mount_storage()
        mock_makedirs.assert_called_with("/mnt/test", exist_ok=True)
        mock_run.assert_called()

class TestPowerStrip(unittest.TestCase):
    def setUp(self):
        self.data = {
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "plugs": {"0": "server1", "1": "server2"}
        }
        self.strip = PowerStrip("kasa1", self.data)

    def test___init__(self):
        self.assertEqual(self.strip.uid, "kasa1")

    def test_get_mac_address(self):
        self.assertEqual(self.strip.get_mac_address(), "AA:BB:CC:DD:EE:FF")

    def test_get_plugs(self):
        self.assertEqual(self.strip.get_plugs()["0"], "server1")

if __name__ == '__main__':
    unittest.main()
