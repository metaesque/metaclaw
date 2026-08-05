import unittest
import asyncio
import os
import tempfile
import json
import io
from unittest.mock import patch, MagicMock, AsyncMock
import power_kasa

class FakeEnergyModule:
    def __init__(self, power, voltage, current):
        self.power = power
        self.voltage = voltage
        self.current = current

class FakePlug:
    def __init__(self, power, voltage, current):
        self.modules = {
            power_kasa.Module.Energy: FakeEnergyModule(power, voltage, current)
        }

class FakeStrip:
    def __init__(self, mac):
        self.mac = mac
        self.device_type = power_kasa.DeviceType.Strip
        self.children = [FakePlug(10.0, 120.0, 0.1) for _ in range(6)]

    async def update(self):
        pass

class TestPowerKasa(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fd, self.config_path = tempfile.mkstemp(suffix=".json")
        test_data = {
            "test_node_valid": {
                "type": "compute_node",
                "price": {
                    "purchased": {
                        "date": "2024-01-01"
                    }
                }
            },
            "test_node_phantom": {
                "type": "compute_node",
                "price": {
                    "purchased": {
                        "date": None
                    }
                }
            },
            "test_strip": {
                "type": "power_strip",
                "mac_address": "AA:BB",
                "plugs": {
                    "0": "test_dev"
                }
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(test_data, f)

    def tearDown(self):
        os.close(self.fd)
        os.remove(self.config_path)

    @patch('power_kasa.Discover.discover', new_callable=AsyncMock)
    @patch('sys.stdout', new_callable=io.StringIO)
    async def test_run_telegraf_export(self, mock_stdout, mock_discover):
        mock_discover.return_value = {"192.168.1.100": FakeStrip("AA:BB")}
        await power_kasa.run_telegraf_export(self.config_path)

        out = mock_stdout.getvalue()

        # Verify metadata emission correctly filters phantom hosts
        self.assertIn("host_metadata,host=test_node_valid active=1i", out)
        self.assertNotIn("test_node_phantom", out)

        # Verify power logic
        self.assertIn("kasa_power,device=test_dev watts=10.000,volts=120.000,amps=0.100", out)

class CleanTestResult(unittest.TextTestResult):
    def getDescription(self, test):
        cls_name = test.__class__.__name__
        if cls_name.startswith('Test'):
            cls_name = cls_name[4:]
        method_name = getattr(test, '_testMethodName', str(test))
        if method_name.startswith('test_'):
            method_name = method_name[5:]
        return f"{cls_name:<25} {method_name:<35}"

class CleanTestRunner(unittest.TextTestRunner):
    resultclass = CleanTestResult

if __name__ == '__main__':
    import sys
    should_buffer = not ('-v' in sys.argv or '--verbose' in sys.argv)
    unittest.main(testRunner=CleanTestRunner, buffer=should_buffer)

